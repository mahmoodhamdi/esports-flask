import logging
from flask import Blueprint, jsonify, request
from app.utils import sanitize_input, allowed_file, save_uploaded_file, is_valid_url, is_valid_thumbnail
from app.news import (
    create_news_item, get_news_items, get_news_by_id,
    update_news_item, delete_news_item, delete_all_news_items
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
import os

logger = logging.getLogger(__name__)
news_bp = Blueprint('news', __name__)

# Rate limiting for production
limiter = Limiter(key_func=get_remote_address)

@news_bp.route('/news', methods=['POST'])
@limiter.limit("10 per minute")
def create_news():
    """
    Create a new news item
    --- 
    tags:
      - News
    summary: Create a new news item with title, writer, and optional details
    consumes:
      - multipart/form-data
    parameters:
      - name: title
        in: formData
        type: string
        required: true
        maxLength: 255
        description: News title
        example: "New Tournament Announced"
      - name: writer
        in: formData
        type: string
        required: true
        maxLength: 100
        description: News author
        example: "John Doe"
      - name: description
        in: formData
        type: string
        required: false
        maxLength: 2000
        description: News description
        example: "A new esports tournament for 2025."
      - name: thumbnail_url
        in: formData
        type: string
        required: false
        description: Thumbnail URL
        example: "https://example.com/thumbnail.jpg"
      - name: thumbnail_file
        in: formData
        type: file
        required: false
        description: Thumbnail image (png, jpg, jpeg, gif, webp)
      - name: news_link
        in: formData
        type: string
        required: false
        description: External news link
        example: "https://example.com/news"
    responses:
      201:
        description: News created
        schema:
          type: object
          properties:
            message:
              type: string
              example: "News created successfully"
            id:
              type: integer
              example: 1
      400:
        description: Invalid input
      413:
        description: File too large
      429:
        description: Too many requests
      500:
        description: Server error
    """
    try:
        title = sanitize_input(request.form.get('title'), 255)
        writer = sanitize_input(request.form.get('writer'), 100)
        description = sanitize_input(request.form.get('description'), 2000)
        thumbnail_url = sanitize_input(request.form.get('thumbnail_url'))
        thumbnail_file = request.files.get('thumbnail_file')
        news_link = sanitize_input(request.form.get('news_link'))

        if not title or not writer:
            return jsonify({"error": "Title and writer are required"}), 400

        if thumbnail_file:
            if thumbnail_file.content_length > 5 * 1024 * 1024:  # 5MB limit
                return jsonify({"error": "File too large, maximum 5MB"}), 413
            if not allowed_file(thumbnail_file.filename):
                return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, webp"}), 400

        result = create_news_item(title, writer, description, thumbnail_url, thumbnail_file, news_link)
        response = jsonify(result)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response, 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"File upload error: {str(e)}")
        return jsonify({"error": "Failed to process file upload"}), 500
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@news_bp.route('/news', methods=['GET'])
@limiter.limit("60 per minute")
def get_news():
    """
    Retrieve paginated news items
    ---
    tags:
      - News
    summary: Get news items with pagination and filters
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        minimum: 1
      - name: per_page
        in: query
        type: integer
        default: 10
        minimum: 1
        maximum: 100
      - name: writer
        in: query
        type: string
        required: false
      - name: search
        in: query
        type: string
        required: false
      - name: sort
        in: query
        type: string
        enum: [created_at, title]
        default: created_at
    responses:
      200:
        description: News items retrieved
      400:
        description: Invalid parameters
      429:
        description: Too many requests
      500:
        description: Server error
    """
    try:
        page = max(1, request.args.get('page', 1, type=int))
        per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
        writer = sanitize_input(request.args.get('writer', ''))
        search = sanitize_input(request.args.get('search', ''))
        sort = request.args.get('sort', 'created_at').strip()
        if sort not in ('created_at', 'title'):
            return jsonify({"error": "Invalid sort parameter"}), 400

        result = get_news_items(page, per_page, writer, search, sort)
        response = jsonify(result)
        response.headers['Cache-Control'] = 'public, max-age=300'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@news_bp.route('/news/<int:id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_news_by_id_route(id):
    """
    Retrieve single news item
    ---
    tags:
      - News
    summary: Get news item by ID
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: News item retrieved
      404:
        description: News item not found
      429:
        description: Too many requests
      500:
        description: Server error
    """
    try:
        result = get_news_by_id(id)
        response = jsonify(result)
        response.headers['Cache-Control'] = 'public, max-age=300'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@news_bp.route('/news/<int:id>', methods=['PUT'])
@limiter.limit("10 per minute")
def update_news(id):
    """
    Update news item
    ---
    tags:
      - News
    summary: Update news item by ID
    consumes:
      - multipart/form-data
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: title
        in: formData
        type: string
        required: false
        maxLength: 255
      - name: writer
        in: formData
        type: string
        required: false
        maxLength: 100
      - name: description
        in: formData
        type: string
        required: false
        maxLength: 2000
      - name: thumbnail_url
        in: formData
        type: string
        required: false
      - name: thumbnail_file
        in: formData
        type: file
        required: false
      - name: news_link
        in: formData
        type: string
        required: false
    responses:
      200:
        description: News updated
      400:
        description: Invalid input
      404:
        description: News item not found
      413:
        description: File too large
      429:
        description: Too many requests
      500:
        description: Server error
    """
    try:
        title = sanitize_input(request.form.get('title'), 255)
        description = sanitize_input(request.form.get('description'), 2000)
        writer = sanitize_input(request.form.get('writer'), 100)
        thumbnail_url = sanitize_input(request.form.get('thumbnail_url'))
        thumbnail_file = request.files.get('thumbnail_file')
        news_link = sanitize_input(request.form.get('news_link'))

        if thumbnail_file:
            if thumbnail_file.content_length > 5 * 1024 * 1024:  # 5MB limit
                return jsonify({"error": "File too large, maximum 5MB"}), 413
            if not allowed_file(thumbnail_file.filename):
                return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, webp"}), 400

        result = update_news_item(id, title, description, writer, thumbnail_url, thumbnail_file, news_link)
        response = jsonify(result)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    except ValueError as e:
        status = 404 if "not found" in str(e).lower() else 400
        return jsonify({"error": str(e)}), status
    except RuntimeError as e:
        logger.error(f"File upload error: {str(e)}")
        return jsonify({"error": "Failed to process file upload"}), 500
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@news_bp.route('/news/<int:id>', methods=['DELETE'])
@limiter.limit("10 per minute")
def delete_news(id):
    """
    Delete news item
    ---
    tags:
      - News
    summary: Delete news item by ID
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: News deleted
      404:
        description: News item not found
      429:
        description: Too many requests
      500:
        description: Server error
    """
    try:
        result = delete_news_item(id)
        response = jsonify(result)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@news_bp.route('/news', methods=['DELETE'])
@limiter.limit("5 per hour")
def delete_all_news():
    """
    Delete all news items
    ---
    tags:
      - News
    summary: Delete all news items and reset ID sequence
    responses:
      200:
        description: All news deleted
      429:
        description: Too many requests
      500:
        description: Server error
    """
    try:
        result = delete_all_news_items()
        response = jsonify(result)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@news_bp.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response