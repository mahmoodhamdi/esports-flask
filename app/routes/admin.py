import sqlite3
import logging
from flask import Blueprint, jsonify, request
from ..db import get_connection, reset_db_sequence
from ..utils import clear_uploads_folder

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/reset_db', methods=['POST'])
def reset_db():
    """
    Reset the database by deleting all data, resetting ID sequence, and optionally clearing uploads
    ---
    consumes:
      - application/json
    parameters:
      - name: clear_uploads
        in: body
        type: boolean
        required: false
        description: Whether to delete all uploaded files in the uploads folder
    responses:
      200:
        description: Database reset successfully
      500:
        description: Database error
    """
    data = request.get_json() or {}
    clear_uploads = data.get('clear_uploads', False)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Delete all data from all tables
        tables = ['news', 'teams', 'events', 'ewc_info', 'games', 'matches', 'transfers', 'prize_distribution']
        for table in tables:
            cursor.execute(f'DELETE FROM {table}')
        
        conn.commit()
        
        # Reset ID sequences
        reset_db_sequence()
        
        # Clear uploads if requested
        if clear_uploads:
            clear_uploads_folder()
        
        return jsonify({"message": "Database reset successfully"})
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()