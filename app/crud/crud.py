import json
import os
from app.db import get_connection

def get_games_from_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT game_name, logo_url FROM games")
    rows = cursor.fetchall()
    conn.close()
    return [{"game_name": row["game_name"], "logo_url": row["logo_url"]} for row in rows]

def store_games_in_db(games_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM games")
    for game in games_data:
        cursor.execute(
            "INSERT INTO games (game_name, logo_url) VALUES (?, ?)",
            (game["game_name"], game["logo_url"])
        )
    conn.commit()
    conn.close()



def get_ewc_rank_from_db():
    if os.path.exists("club_championship_standings_api.json"):
        with open("club_championship_standings_api.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def store_ewc_rank_in_db(data):
    with open("club_championship_standings_api.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


