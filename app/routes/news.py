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
    """Create a new news item."""
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
    """Retrieve a list of news items with pagination, filtering, and sorting."""
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
    """Retrieve a single news item by ID."""
    try:
        result = get_news_by_id(id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@news_bp.route('/news/<int:id>', methods=['PUT'])
def update_news(id):
    """Update an existing news item by ID."""
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
    """Delete a news item by ID."""
    try:
        result = delete_news_item(id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@news_bp.route('/news', methods=['DELETE'])
def delete_all_news():
    """Delete all news items and reset ID sequence."""
    try:
        result = delete_all_news_items()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500