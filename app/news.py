import sqlite3
import logging
from datetime import datetime
from app.db import get_connection
from app.utils import save_uploaded_file, is_valid_url, is_valid_thumbnail, sanitize_input, allowed_file
import os
logger = logging.getLogger(__name__)

# Base URL for constructing full image URLs (configure for production)
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

def create_news_item(title, writer, description, thumbnail_url, thumbnail_file, news_link):
    """Create a new news item with validation."""
    if not title or not writer:
        raise ValueError("Title and writer are required")

    title = sanitize_input(title, 255)
    writer = sanitize_input(writer, 100)
    description = sanitize_input(description, 2000) if description else None
    news_link = sanitize_input(news_link) if news_link else None
    final_thumbnail_url = None

    if thumbnail_file and thumbnail_url:
        raise ValueError("Provide either thumbnail file or URL, not both")

    if thumbnail_file:
        logger.debug(f"Received file: {thumbnail_file.filename}")
        if not allowed_file(thumbnail_file.filename):
            raise ValueError("Invalid file type. Allowed: png, jpg, jpeg, gif, webp")
        final_thumbnail_url = save_uploaded_file(thumbnail_file)
        if not final_thumbnail_url:
            raise RuntimeError("Failed to save uploaded file")
        # Convert relative path to full URL
        if final_thumbnail_url.startswith('/'):
            final_thumbnail_url = f"{BASE_URL}{final_thumbnail_url}"
    
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
        cursor.execute('''
            INSERT INTO news (title, description, writer, thumbnail_url, news_link, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, writer, final_thumbnail_url, news_link, 
              datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        conn.commit()
        news_id = cursor.lastrowid
        logger.info(f"Created news item {news_id}")
        return {"message": "News created successfully", "id": news_id}
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()

def get_news_items(page=1, per_page=10, writer='', search='', sort='created_at'):
    """Retrieve paginated news items with optimized queries."""
    page = max(1, page)
    per_page = max(1, min(100, per_page))
    sort = 'created_at' if sort not in ('created_at', 'title') else sort

    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        if search:
            query = '''
                SELECT n.id, n.title, n.description, n.writer, n.thumbnail_url, n.news_link, 
                       n.created_at, n.updated_at 
                FROM news n
                JOIN news_fts ON n.id = news_fts.rowid
                WHERE news_fts MATCH ?'''
            params = [search]
            
            if writer:
                query += ' AND writer LIKE ?'
                params.append(f'%{sanitize_input(writer)}%')
        else:
            query = '''
                SELECT id, title, description, writer, thumbnail_url, news_link, 
                       created_at, updated_at 
                FROM news WHERE 1=1'''
            params = []
            
            if writer:
                query += ' AND writer LIKE ?'
                params.append(f'%{sanitize_input(writer)}%')

        query += f' ORDER BY {sort} DESC LIMIT ? OFFSET ?'
        params.extend([per_page, (page - 1) * per_page])

        cursor.execute(query, params)
        news_items = [
            {
                'id': row[0], 
                'title': row[1], 
                'description': row[2] or '', 
                'writer': row[3],
                'thumbnail_url': f"{BASE_URL}{row[4]}" if row[4] and row[4].startswith('/') else (row[4] or ''), 
                'news_link': row[5] or '', 
                'created_at': row[6], 
                'updated_at': row[7]
            } for row in cursor.fetchall()
        ]

        count_query = 'SELECT COUNT(*) FROM news WHERE 1=1'
        count_params = []
        if writer:
            count_query += ' AND writer LIKE ?'
            count_params.append(f'%{sanitize_input(writer)}%')
        if search and not writer:
            count_query = 'SELECT COUNT(*) FROM news_fts WHERE news_fts MATCH ?'
            count_params = [search]

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
    """Retrieve single news item with validation."""
    if not isinstance(id, int) or id <= 0:
        raise ValueError("Invalid news ID")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, description, writer, thumbnail_url, news_link, created_at, updated_at 
            FROM news WHERE id = ?
        ''', (id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("News item not found")

        return {
            'id': row[0], 
            'title': row[1], 
            'description': row[2] or '', 
            'writer': row[3],
            'thumbnail_url': f"{BASE_URL}{row[4]}" if row[4] and row[4].startswith('/') else (row[4] or ''), 
            'news_link': row[5] or '', 
            'created_at': row[6], 
            'updated_at': row[7]
        }
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()

def update_news_item(id, title, description, writer, thumbnail_url, thumbnail_file, news_link):
    """Update news item with validation and cleanup."""
    if not isinstance(id, int) or id <= 0:
        raise ValueError("Invalid news ID")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, thumbnail_url FROM news WHERE id = ?', (id,))
        existing = cursor.fetchone()
        if not existing:
            raise ValueError("News item not found")

        update_data = {}
        if title:
            update_data['title'] = sanitize_input(title, 255)
        if description:
            update_data['description'] = sanitize_input(description, 2000)
        if writer:
            update_data['writer'] = sanitize_input(writer, 100)
        if news_link:
            news_link = sanitize_input(news_link)
            if not is_valid_url(news_link):
                raise ValueError("Invalid news link URL")
            update_data['news_link'] = news_link

        final_thumbnail_url = None
        if thumbnail_file and thumbnail_url:
            raise ValueError("Provide either thumbnail file or URL, not both")

        if thumbnail_file:
            if not allowed_file(thumbnail_file.filename):
                raise ValueError("Invalid file type. Allowed: png, jpg, jpeg, gif, webp")
            final_thumbnail_url = save_uploaded_file(thumbnail_file)
            if not final_thumbnail_url:
                raise RuntimeError("Failed to save uploaded file")
            update_data['thumbnail_url'] = f"{BASE_URL}{final_thumbnail_url}"
        elif thumbnail_url:
            if not is_valid_thumbnail(thumbnail_url):
                raise ValueError("Invalid thumbnail URL")
            update_data['thumbnail_url'] = thumbnail_url

        if not update_data:
            raise ValueError("No data provided to update")

        update_data['updated_at'] = datetime.utcnow().isoformat()

        set_clause = ', '.join(f'{key} = ?' for key in update_data.keys())
        query = f'UPDATE news SET {set_clause} WHERE id = ?'
        params = list(update_data.values()) + [id]

        cursor.execute(query, params)
        conn.commit()

        if 'thumbnail_url' in update_data and existing[1] and existing[1].startswith(BASE_URL):
            try:
                file_path = existing[1].replace(BASE_URL, '')[1:]  # Remove base URL and leading slash
                os.remove(file_path)
                logger.debug(f"Removed old thumbnail: {existing[1]}")
            except OSError as e:
                logger.warning(f"Failed to remove old thumbnail: {str(e)}")

        logger.info(f"Updated news item {id}")
        return {"message": "News updated successfully"}
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()

def delete_news_item(id):
    """Delete news item and its thumbnail."""
    if not isinstance(id, int) or id <= 0:
        raise ValueError("Invalid news ID")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, thumbnail_url FROM news WHERE id = ?', (id,))
        existing = cursor.fetchone()
        if not existing:
            raise ValueError("News item not found")

        cursor.execute('DELETE FROM news WHERE id = ?', (id,))
        conn.commit()

        if existing[1] and existing[1].startswith(BASE_URL):
            try:
                file_path = existing[1].replace(BASE_URL, '')[1:]  # Remove base URL and leading slash
                os.remove(file_path)
                logger.debug(f"Removed thumbnail: {existing[1]}")
            except OSError as e:
                logger.warning(f"Failed to remove thumbnail: {str(e)}")

        logger.info(f"Deleted news item {id}")
        return {"message": "News deleted successfully"}
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()

def delete_all_news_items():
    """Delete all news items and clean up."""
    from app.db import reset_db_sequence
    from app.utils import clear_uploads_folder

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM news')
        conn.commit()
        reset_db_sequence()
        clear_uploads_folder()
        logger.info("Deleted all news items and reset sequence")
        return {"message": "All news items deleted successfully and ID sequence reset"}
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()