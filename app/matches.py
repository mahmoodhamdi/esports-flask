import sqlite3
from app.utils import get_html_via_api, extract_matches_from_html
from datetime import datetime

def fetch_group_matches(game: str, tournament: str) -> dict:
    """Fetch group stage matches from Liquipedia"""
    page = f"{tournament}/Group_Stage"
    html = get_html_via_api(game, page)
    if html is None or html.strip() == "":
        page = tournament
        html = get_html_via_api(game, page)
        if html is None or html.strip() == "":
            return {"status": "missing_page", "matches": None}

    matches = extract_matches_from_html(html)
    if not matches:
        return {"status": "no_matches", "matches": None}
    return {"status": "ok", "matches": matches}

def save_group_matches_to_db(game: str, tournament: str, matches_by_group: dict):
    """Save group stage matches to SQLite database"""
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game TEXT,
            tournament TEXT,
            group_name TEXT,
            team1_name TEXT,
            team1_logo TEXT,
            team2_name TEXT,
            team2_logo TEXT,
            match_time TEXT,
            score TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    for group, matches in matches_by_group.items():
        for match in matches:
            cursor.execute('''
                INSERT OR REPLACE INTO group_matches (
                    game, tournament, group_name,
                    team1_name, team1_logo,
                    team2_name, team2_logo,
                    match_time, score, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game,
                tournament,
                group,
                match["Team1"]["Name"],
                match["Team1"]["Logo"],
                match["Team2"]["Name"],
                match["Team2"]["Logo"],
                match["MatchTime"],
                match["Score"],
                datetime.utcnow()
            ))

    conn.commit()
    conn.close()

def get_group_matches(game: str, tournament: str, group_name: str = None, start_date: str = None, end_date: str = None) -> list:
    """Retrieve matches from database with optional filters"""
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    query = '''
        SELECT id, game, tournament, group_name,
               team1_name, team1_logo, team2_name, team2_logo,
               match_time, score, created_at, updated_at
        FROM group_matches
        WHERE game = ? AND tournament = ?
    '''
    params = [game, tournament]

    if group_name:
        query += " AND group_name = ?"
        params.append(group_name)
    if start_date:
        query += " AND date(match_time) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date(match_time) <= ?"
        params.append(end_date)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [{
        "id": row[0],
        "game": row[1],
        "tournament": row[2],
        "group_name": row[3],
        "team1": {"name": row[4], "logo": row[5]},
        "team2": {"name": row[6], "logo": row[7]},
        "match_time": row[8],
        "score": row[9],
        "created_at": row[10],
        "updated_at": row[11]
    } for row in rows]

def update_group_matches(game: str, tournament: str, group_name: str, match_id: int, update_data: dict) -> bool:
    """Update a specific match in the database"""
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    set_clause = []
    params = []
    for key, value in update_data.items():
        if value is not None:
            set_clause.append(f"{key} = ?")
            params.append(value)

    if not set_clause:
        conn.close()
        return False

    params.extend([datetime.utcnow(), game, tournament, group_name, match_id])
    query = f'''
        UPDATE group_matches
        SET {', '.join(set_clause)}, updated_at = ?
        WHERE game = ? AND tournament = ? AND group_name = ? AND id = ?
    '''

    cursor.execute(query, params)
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0

def delete_group_matches(game: str, tournament: str, group_name: str = None, match_id: str = None) -> int:
    """Delete matches from database with optional filters"""
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    query = "DELETE FROM group_matches WHERE game = ? AND tournament = ?"
    params = [game, tournament]

    if group_name:
        query += " AND group_name = ?"
        params.append(group_name)
    if match_id:
        query += " AND id = ?"
        params.append(match_id)

    cursor.execute(query, params)
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted