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
    Reset the entire database and optionally delete uploaded files.

    This endpoint will:
      - Delete all data from critical tables.
      - Reset all auto-incrementing ID sequences.
      - Optionally delete all uploaded files in the `uploads/` directory.

    ---
    tags:
      - Admin
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: false
        description: Optional configuration for database reset
        schema:
          type: object
          properties:
            clear_uploads:
              type: boolean
              default: false
              description: |
                If true, all files inside the uploads directory will be deleted.
    responses:
      200:
        description: Database reset successfully
        examples:
          application/json:
            {
              "message": "Database reset successfully"
            }
      500:
        description: Internal server error during database reset
        examples:
          application/json:
            {
              "error": "Database error: table 'xyz' does not exist"
            }
    """
    data = request.get_json() or {}
    clear_uploads = data.get('clear_uploads', False)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Delete all data from all tables
        tables = ['news','teams','events','ewc_info','games','matches','transfers','prize_distribution','group_matches','global_matches']
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