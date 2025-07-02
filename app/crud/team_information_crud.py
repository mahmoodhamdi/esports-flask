import json
from app.db import get_connection

def get_team_info(game: str, team_page_name: str) -> dict | None:
    """Retrieve team information from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT data FROM team_information
            WHERE game = ? AND team_page_name = ?
        ''', (game, team_page_name))
        row = cursor.fetchone()
        return json.loads(row['data']) if row else None
    except Exception as e:
        print(f"Error retrieving team info: {e}")
        return None
    finally:
        conn.close()

def save_team_info(game: str, team_page_name: str, data: dict) -> bool:
    """Save or update team information in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO team_information (game, team_page_name, data)
            VALUES (?, ?, ?)
        ''', (game, team_page_name, json.dumps(data)))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving team info: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()