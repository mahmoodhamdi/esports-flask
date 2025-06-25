import sqlite3
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from ..db import get_connection
from ..utils import (
    save_uploaded_file, 
    is_valid_url, 
    is_valid_thumbnail, 
    sanitize_input,
    allowed_file
)

logger = logging.getLogger(__name__)
news_bp = Blueprint('news', __name__)

@news_bp.route('/news', methods=['POST'])
def create_news():
    """
    Create a new news item
    ---
    consumes:
      - multipart/form-data
      - application/json
    parameters:
      - name: title
        in: formData
        type: string
        required: true
      - name: writer
        in: formData
        type: string
        required: true
      - name: description
        in: formData
        type: string
      - name: thumbnail_url
        in: formData
        type: string
      - name: thumbnail_file
        in: formData
        type: file
      - name: news_link
        in: formData
        type: string
    responses:
      201:
        description: News item created successfully
      400:
        description: Invalid input data
    """
    title = sanitize_input(request.form.get('title'), 255)
    writer = sanitize_input(request.form.get('writer'), 100)
    description = sanitize_input(request.form.get('description'), 2000)
    thumbnail_url = sanitize_input(request.form.get('thumbnail_url'))
    news_link = sanitize_input(request.form.get('news_link'))
    
    if not title or not writer:
        return jsonify({"error": "Title and writer are required"}), 400
    
    final_thumbnail_url = ''
    
    # Handle file upload
    if 'thumbnail_file' in request.files and request.files['thumbnail_file']:
        file = request.files['thumbnail_file']
        logger.debug(f"Received file: {file.filename if file else 'None'}")
        
        if file and allowed_file(file.filename):
            final_thumbnail_url = save_uploaded_file(file)
            if not final_thumbnail_url:
                return jsonify({"error": "Failed to save uploaded file"}), 500
            logger.debug(f"Set final_thumbnail_url to: {final_thumbnail_url}")
        else:
            return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, webp"}), 400
    
    # Handle URL thumbnail
    elif thumbnail_url:
        logger.debug(f"Received thumbnail_url: {thumbnail_url}")
        if not is_valid_thumbnail(thumbnail_url):
            return jsonify({"error": "Invalid thumbnail URL"}), 400
        final_thumbnail_url = thumbnail_url
        logger.debug(f"Set final_thumbnail_url to: {final_thumbnail_url}")
    
    # Validate news link
    if news_link and not is_valid_url(news_link):
        return jsonify({"error": "Invalid news link URL"}), 400
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.debug(f"Inserting news item with thumbnail_url: {final_thumbnail_url}")
        cursor.execute('''
            INSERT INTO news (title, description, writer, thumbnail_url, news_link)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, writer, final_thumbnail_url, news_link))
        
        conn.commit()
        news_id = cursor.lastrowid
        
        # Verify saved data
        cursor.execute('SELECT thumbnail_url FROM news WHERE id = ?', (news_id,))
        saved_thumbnail_url = cursor.fetchone()[0]
        logger.debug(f"Saved thumbnail_url in DB: {saved_thumbnail_url}")
        
        return jsonify({
            "message": "News created successfully",
            "id": news_id
        }), 201
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@news_bp.route('/news', methods=['GET'])
def get_news():
    """
    Get news items with pagination and filtering
    ---
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
      - name: writer
        in: query
        type: string
      - name: search
        in: query
        type: string
      - name: sort
        in: query
        type: string
        enum: [created_at, title]
        default: created_at
    responses:
      200:
        description: List of news items
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    writer = sanitize_input(request.args.get('writer', ''))
    search = sanitize_input(request.args.get('search', ''))
    sort = request.args.get('sort', 'created_at').strip()
    
    if sort not in ('created_at', 'title'):
        sort = 'created_at'
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build query
        query = '''
            SELECT id, title, description, writer, thumbnail_url, news_link, created_at, updated_at 
            FROM news WHERE 1=1
        '''
        params = []
        
        if writer:
            query += ' AND writer LIKE ?'
            params.append(f'%{writer}%')
        
        if search:
            query += ' AND (title LIKE ? OR description LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += f' ORDER BY {sort} DESC'
        query += ' LIMIT ? OFFSET ?'
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        news_items = [
            {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'writer': row[3],
                'thumbnail_url': row[4] or '',
                'news_link': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            } for row in cursor.fetchall()
        ]
        
        logger.debug(f"Retrieved news items: {[item['thumbnail_url'] for item in news_items]}")
        
        # Get total count
        count_query = 'SELECT COUNT(*) FROM news WHERE 1=1'
        count_params = []
        
        if writer:
            count_query += ' AND writer LIKE ?'
            count_params.append(f'%{writer}%')
        
        if search:
            count_query += ' AND (title LIKE ? OR description LIKE ?)'
            count_params.extend([f'%{search}%', f'%{search}%'])
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        return jsonify({
            'news': news_items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@news_bp.route('/news/<int:id>', methods=['PUT'])
def update_news(id):
    """
    Update an existing news item
    ---
    consumes:
      - multipart/form-data
      - application/json
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: title
        in: formData
        type: string
      - name: description
        in: formData
        type: string
      - name: writer
        in: formData
        type: string
      - name: thumbnail_url
        in: formData
        type: string
      - name: thumbnail_file
        in: formData
        type: file
      - name: news_link
        in: formData
        type: string
    responses:
      200:
        description: News item updated successfully
      404:
        description: News item not found
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if news item exists
        cursor.execute('SELECT id FROM news WHERE id = ?', (id,))
        if not cursor.fetchone():
            return jsonify({"error": "News item not found"}), 404
        
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    title = sanitize_input(request.form.get('title'), 255)
    description = sanitize_input(request.form.get('description'), 2000)
    writer = sanitize_input(request.form.get('writer'), 100)
    thumbnail_url = sanitize_input(request.form.get('thumbnail_url'))
    news_link = sanitize_input(request.form.get('news_link'))
    
    final_thumbnail_url = None
    
    # Handle file upload
    if 'thumbnail_file' in request.files and request.files['thumbnail_file']:
        file = request.files['thumbnail_file']
        logger.debug(f"Received file for update: {file.filename if file else 'None'}")
        
        if file and allowed_file(file.filename):
            final_thumbnail_url = save_uploaded_file(file)
            if not final_thumbnail_url:
                return jsonify({"error": "Failed to save uploaded file"}), 500
            logger.debug(f"Set final_thumbnail_url for update to: {final_thumbnail_url}")
        else:
            return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, webp"}), 400
    
    # Handle URL thumbnail
    elif thumbnail_url:
        logger.debug(f"Received thumbnail_url for update: {thumbnail_url}")
        if not is_valid_thumbnail(thumbnail_url):
            return jsonify({"error": "Invalid thumbnail URL"}), 400
        final_thumbnail_url = thumbnail_url
        logger.debug(f"Set final_thumbnail_url for update to: {final_thumbnail_url}")
    
    # Validate news link
    if news_link and not is_valid_url(news_link):
        return jsonify({"error": "Invalid news link URL"}), 400
    
    # Build update data
    update_data = {}
    if title:
        update_data['title'] = title
    if description:
        update_data['description'] = description
    if writer:
        update_data['writer'] = writer
    if final_thumbnail_url is not None:
        update_data['thumbnail_url'] = final_thumbnail_url
    if news_link:
        update_data['news_link'] = news_link
    
    if not update_data:
        return jsonify({"error": "No data provided to update"}), 400
    
    update_data['updated_at'] = datetime.utcnow().isoformat()
    
    try:
        set_clause = ', '.join(f'{key} = ?' for key in update_data.keys())
        query = f'UPDATE news SET {set_clause} WHERE id = ?'
        params = list(update_data.values()) + [id]
        
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({"message": "News updated successfully"})
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@news_bp.route('/news/<int:id>', methods=['DELETE'])
def delete_news(id):
    """
    Delete a news item
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: News item deleted successfully
      404:
        description: News item not found
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM news WHERE id = ?', (id,))
        if not cursor.fetchone():
            return jsonify({"error": "News item not found"}), 404
        
        cursor.execute('DELETE FROM news WHERE id = ?', (id,))
        conn.commit()
        
        return jsonify({"message": "News deleted successfully"})
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@news_bp.route('/news', methods=['DELETE'])
def delete_all_news():
    """
    Delete all news items and reset ID sequence
    ---
    responses:
      200:
        description: All news items deleted successfully
      500:
        description: Database error
    """
    try:
        from ..db import reset_db_sequence
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM news')
        conn.commit()
        
        reset_db_sequence()
        
        return jsonify({"message": "All news items deleted successfully and ID sequence reset"})
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()