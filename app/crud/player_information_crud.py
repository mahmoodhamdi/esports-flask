import json
from app.db import get_connection
def get_player_info(game: str, player_page_name: str) -> dict | None:
    """Retrieve player information from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT data FROM player_information
            WHERE game = ? AND player_page_name = ?
        ''', (game, player_page_name))
        row = cursor.fetchone()
        if row:
            data = json.loads(row['data'])
            # ✂️ احذف الـ Upcoming_Matches لو موجودة
            data.pop("Upcoming_Matches", None)

            return data
        else:
            return None
    except Exception as e:
        print(f"Error retrieving player info: {e}")
        return None
    finally:
        conn.close()


def save_player_info(game: str, player_page_name: str, data: dict) -> bool:
    """Save or update player information in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO player_information (game, player_page_name, data)
            VALUES (?, ?, ?)
        ''', (game, player_page_name, json.dumps(data)))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving player info: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()