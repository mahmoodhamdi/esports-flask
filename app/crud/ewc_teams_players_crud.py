from app.db import get_connection
import json

def insert_ewc_team_player_data(game, team_name, placement, tournament, tournament_logo, years, players, hash_value):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO ewc_teams_players (game, team_name, placement, tournament, tournament_logo, years, players, hash_value) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (game, team_name, placement, tournament, tournament_logo, years, json.dumps(players), hash_value)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error inserting EWC team player data: {e}")
        return None
    finally:
        conn.close()

def get_ewc_team_player_data(game, team_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM ewc_teams_players WHERE game = ? AND team_name = ? ORDER BY updated_at DESC LIMIT 1",
            (game, team_name)
        )
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data['players'] = json.loads(data['players'])
            return data
        return None
    except Exception as e:
        print(f"Error retrieving EWC team player data: {e}")
        return None
    finally:
        conn.close()

def update_ewc_team_player_data(game, team_name, placement, tournament, tournament_logo, years, players, hash_value):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE ewc_teams_players SET placement = ?, tournament = ?, tournament_logo = ?, years = ?, players = ?, hash_value = ?, updated_at = CURRENT_TIMESTAMP WHERE game = ? AND team_name = ?",
            (placement, tournament, tournament_logo, years, json.dumps(players), hash_value, game, team_name)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating EWC team player data: {e}")
        return False
    finally:
        conn.close()

def get_all_ewc_team_player_data(game):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM ewc_teams_players WHERE game = ? ORDER BY updated_at DESC",
            (game,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            data = dict(row)
            data['players'] = json.loads(data['players'])
            result.append(data)
        return result
    except Exception as e:
        print(f"Error retrieving all EWC team player data: {e}")
        return None
    finally:
        conn.close()


