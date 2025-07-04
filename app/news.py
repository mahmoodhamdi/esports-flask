import sqlite3
import logging
from flask import request  # Added import
from datetime import datetime
from app.db import get_connection
from app.utils import save_uploaded_file, is_valid_url, is_valid_thumbnail, sanitize_input, allowed_file

logger = logging.getLogger(__name__)


def create_news_item(title, writer, description, thumbnail_url, thumbnail_file,
                     news_link):
    """Create a new news item."""
    if not title or not writer:
        raise ValueError("Title and writer are required")

    final_thumbnail_url = ''

    if thumbnail_file:
        logger.debug(f"Received file: {thumbnail_file.filename}")
        if allowed_file(thumbnail_file.filename):
            filename = save_uploaded_file(thumbnail_file)
            if filename:
                final_thumbnail_url = f"{request.host_url.rstrip('/')}/uploads/{filename}"
                logger.debug(
                    f"Saved file: {final_thumbnail_url}")  # Added debug log
            else:
                raise RuntimeError("Failed to save uploaded file")
        else:
            raise ValueError(
                "Invalid file type. Allowed: png, jpg, jpeg, gif, webp")
    elif thumbnail_url:
        logger.debug(f"Received thumbnail_url: {thumbnail_url}")
        if not is_valid_thumbnail(thumbnail_url):
            raise ValueError("Invalid thumbnail URL")
        final_thumbnail_url = thumbnail_url

    if news_link and not is_valid_url(news_link):
        raise ValueError("Invalid news link URL")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO news (title, description, writer, thumbnail_url, news_link)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, writer, final_thumbnail_url, news_link))
        conn.commit()
        news_id = cursor.lastrowid
        return {"message": "News created successfully", "id": news_id}
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()


def update_news_item(id, title, description, writer, thumbnail_url,
                     thumbnail_file, news_link):
    """Update an existing news item by ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM news WHERE id = ?', (id, ))
        if not cursor.fetchone():
            raise ValueError("News item not found")
    except sqlite3.Error as e:
        raise

    final_thumbnail_url = None
    if thumbnail_file:
        logger.debug(f"Received file for update: {thumbnail_file.filename}")
        if allowed_file(thumbnail_file.filename):
            filename = save_uploaded_file(thumbnail_file)
            if filename:
                final_thumbnail_url = f"{request.host_url.rstrip('/')}/uploads/{filename}"
            else:
                raise RuntimeError("Failed to save uploaded file")
        else:
            raise ValueError(
                "Invalid file type. Allowed: png, jpg, jpeg, gif, webp")
    elif thumbnail_url:
        logger.debug(f"Received thumbnail_url for update: {thumbnail_url}")
        if not is_valid_thumbnail(thumbnail_url):
            raise ValueError("Invalid thumbnail URL")
        final_thumbnail_url = thumbnail_url

    if news_link and not is_valid_url(news_link):
        raise ValueError("Invalid news link URL")

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
        raise ValueError("No data provided to update")

    update_data['updated_at'] = datetime.utcnow().isoformat()

    try:
        cursor = conn.cursor()
        set_clause = ', '.join(f'{key} = ?' for key in update_data.keys())
        query = f'UPDATE news SET {set_clause} WHERE id = ?'
        params = list(update_data.values()) + [id]

        cursor.execute(query, params)
        conn.commit()
        return {"message": "News updated successfully"}
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()


def get_news_items(page=1,
                   per_page=10,
                   writer='',
                   search='',
                   sort='created_at'):
    """Retrieve paginated news items with filtering and sorting."""
    page = max(1, page)
    per_page = max(1, min(100, per_page))
    if sort not in ('created_at', 'title'):
        sort = 'created_at'

    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = '''SELECT id, title, description, writer, thumbnail_url, news_link, created_at, updated_at 
                   FROM news WHERE 1=1'''
        params = []

        if writer:
            query += ' AND writer LIKE ?'
            params.append(f'%{writer}%')

        if search:
            query += ' AND (title LIKE ? OR description LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])

        query += f' ORDER BY {sort} DESC LIMIT ? OFFSET ?'
        params.extend([per_page, (page - 1) * per_page])

        cursor.execute(query, params)
        news_items = [{
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'writer': row[3],
            'thumbnail_url': row[4] or '',
            'news_link': row[5],
            'created_at': row[6],
            'updated_at': row[7]
        } for row in cursor.fetchall()]

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

        return {
            'news': news_items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()


def get_news_by_id(id):
    """Retrieve a single news item by ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT id, title, description, writer, thumbnail_url, news_link, created_at, updated_at 
            FROM news WHERE id = ?
        ''', (id, ))
        row = cursor.fetchone()
        if not row:
            raise ValueError("News item not found")

        return {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'writer': row[3],
            'thumbnail_url': row[4] or '',
            'news_link': row[5],
            'created_at': row[6],
            'updated_at': row[7]
        }
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()


def delete_news_item(id):
    """Delete a news item by ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM news WHERE id = ?', (id, ))
        if not cursor.fetchone():
            raise ValueError("News item not found")

        cursor.execute('DELETE FROM news WHERE id = ?', (id, ))
        conn.commit()
        return {"message": "News deleted successfully"}
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()


def delete_all_news_items():
    """Delete all news items and reset ID sequence."""
    from app.db import reset_db_sequence
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM news')
        conn.commit()
        reset_db_sequence()
        return {
            "message":
            "All news items deleted successfully and ID sequence reset"
        }
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()
