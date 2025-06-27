import logging
from flask import Blueprint, jsonify, request
from app.utils import sanitize_input
from app.news import (
    create_news_item, get_news_items, get_news_by_id,
    update_news_item, delete_news_item, delete_all_news_items
)

logger = logging.getLogger(__name__)
news_bp = Blueprint('news', __name__)

@news_bp.route('/news', methods=['POST'])
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
        description: The title of the news item
        example: "New Tournament Announced"
      - name: writer
        in: formData
        type: string
        required: true
        maxLength: 100
        description: The author of the news item
        example: "John Doe"
      - name: description
        in: formData
        type: string
        required: false
        maxLength: 2000
        description: Detailed description of the news item
        example: "A new esports tournament has been announced for 2025."
      - name: thumbnail_url
        in: formData
        type: string
        required: false
        description: URL of the thumbnail image
        example: "https://example.com/thumbnail.jpg"
      - name: thumbnail_file
        in: formData
        type: file
        required: false
        description: Thumbnail image file (png, jpg, jpeg, gif, webp)
      - name: news_link
        in: formData
        type: string
        required: false
        description: External link to the full news article
        example: "https://example.com/news"
    responses:
      201:
        description: News item created successfully
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
        description: Missing or invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Title and writer are required"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Database error: ..."
    """
    title = sanitize_input(request.form.get('title'), 255)
    writer = sanitize_input(request.form.get('writer'), 100)
    description = sanitize_input(request.form.get('description'), 2000)
    thumbnail_url = sanitize_input(request.form.get('thumbnail_url'))
    thumbnail_file = request.files.get('thumbnail_file')
    news_link = sanitize_input(request.form.get('news_link'))
    
    try:
        result = create_news_item(title, writer, description, thumbnail_url, thumbnail_file, news_link)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@news_bp.route('/news', methods=['GET'])
def get_news():
    """
    Retrieve a list of news items with pagination, filtering, and sorting
    ---
    tags:
      - News
    summary: Get a paginated list of news items with optional filters
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        minimum: 1
        description: Page number for pagination
        example: 1
      - name: per_page
        in: query
        type: integer
        default: 10
        minimum: 1
        maximum: 100
        description: Number of items per page
        example: 10
      - name: writer
        in: query
        type: string
        required: false
        description: Filter by writer name (partial match)
        example: "John Doe"
      - name: search
        in: query
        type: string
        required: false
        description: Search in title and description (partial match)
        example: "tournament"
      - name: sort
        in: query
        type: string
        enum: [created_at, title]
        default: created_at
        description: Sort field (descending)
        example: "created_at"
    responses:
      200:
        description: Paginated list of news items
        schema:
          type: object
          properties:
            news:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  title:
                    type: string
                    example: "New Tournament Announced"
                  description:
                    type: string
                    example: "A new esports tournament has been announced for 2025."
                  writer:
                    type: string
                    example: "John Doe"
                  thumbnail_url:
                    type: string
                    example: "https://example.com/thumbnail.jpg"
                  news_link:
                    type: string
                    example: "https://example.com/news"
                  created_at:
                    type: string
                    example: "2025-06-28T02:45:00Z"
                  updated_at:
                    type: string
                    example: "2025-06-28T02:45:00Z"
            pagination:
              type: object
              properties:
                page:
                  type: integer
                  example: 1
                per_page:
                  type: integer
                  example: 10
                total:
                  type: integer
                  example: 50
                pages:
                  type: integer
                  example: 5
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Database error: ..."
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    writer = sanitize_input(request.args.get('writer', ''))
    search = sanitize_input(request.args.get('search', ''))
    sort = request.args.get('sort', 'created_at').strip()
    
    try:
        result = get_news_items(page, per_page, writer, search, sort)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@news_bp.route('/news/<int:id>', methods=['GET'])
def get_news_by_id_route(id):
    """
    Retrieve a single news item by ID
    ---
    tags:
      - News
    summary: Get details of a specific news item by its ID
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID of the news item to retrieve
        example: 1
    responses:
      200:
        description: News item retrieved successfully
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            title:
              type: string
              example: "New Tournament Announced"
            description:
              type: string
              example: "A new esports tournament has been announced for 2025."
            writer:
              type: string
              example: "John Doe"
            thumbnail_url:
              type: string
              example: "https://example.com/thumbnail.jpg"
            news_link:
              type: string
              example: "https://example.com/news"
            created_at:
              type: string
              example: "2025-06-28T02:45:00Z"
            updated_at:
              type: string
              example: "2025-06-28T02:45:00Z"
      404:
        description: News item not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "News item not found"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Database error: ..."
    """
    try:
        result = get_news_by_id(id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@news_bp.route('/news/<int:id>', methods=['PUT'])
def update_news(id):
    """
    Update an existing news item by ID
    ---
    tags:
      - News
    summary: Update details of a specific news item
    consumes:
      - multipart/form-data
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID of the news item to update
        example: 1
      - name: title
        in: formData
        type: string
        required: false
        maxLength: 255
        description: Updated title of the news item
        example: "Updated Tournament News"
      - name: writer
        in: formData
        type: string
        required: false
        maxLength: 100
        description: Updated writer name
        example: "Jane Doe"
      - name: description
        in: formData
        type: string
        required: false
        maxLength: 2000
        description: Updated description
        example: "Updated details for the 2025 tournament."
      - name: thumbnail_url
        in: formData
        type: string
        required: false
        description: New thumbnail URL
        example: "https://example.com/new_thumbnail.jpg"
      - name: thumbnail_file
        in: formData
        type: file
        required: false
        description: New thumbnail image file (png, jpg, jpeg, gif, webp)
      - name: news_link
        in: formData
        type: string
        required: false
        description: Updated external news link
        example: "https://example.com/updated_news"
    responses:
      200:
        description: News item updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "News updated successfully"
      400:
        description: Invalid update data
        schema:
          type: object
          properties:
            error:
              type: string
              example: "No data provided to update"
      404:
        description: News item not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "News item not found"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Database error: ..."
    """
    title = sanitize_input(request.form.get('title'), 255)
    description = sanitize_input(request.form.get('description'), 2000)
    writer = sanitize_input(request.form.get('writer'), 100)
    thumbnail_url = sanitize_input(request.form.get('thumbnail_url'))
    thumbnail_file = request.files.get('thumbnail_file')
    news_link = sanitize_input(request.form.get('news_link'))
    
    try:
        result = update_news_item(id, title, description, writer, thumbnail_url, thumbnail_file, news_link)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400 if "not found" not in str(e).lower() else 404
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@news_bp.route('/news/<int:id>', methods=['DELETE'])
def delete_news(id):
    """
    Delete a news item by ID
    ---
    tags:
      - News
    summary: Delete a specific news item by its ID
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID of the news item to delete
        example: 1
    responses:
      200:
        description: News item deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "News deleted successfully"
      404:
        description: News item not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "News item not found"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Database error: ..."
    """
    try:
        result = delete_news_item(id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@news_bp.route('/news', methods=['DELETE'])
def delete_all_news():
    """
    Delete all news items and reset ID sequence
    ---
    tags:
      - News
    summary: Delete all news items and reset the ID sequence
    responses:
      200:
        description: All news items deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "All news items deleted successfully and ID sequence reset"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Database error: ..."
    """
    try:
        result = delete_all_news_items()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500