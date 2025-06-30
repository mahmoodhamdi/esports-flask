from app.db import get_connection
import json
import sqlite3

def insert_ewc_team_player_data(game, team_name, placement, tournament, tournament_logo, years, players, hash_value):
    """Insert new EWC team player data"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO ewc_teams_players 
               (game, team_name, placement, tournament, tournament_logo, years, players, hash_value) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (game, team_name, placement, tournament, tournament_logo, years, json.dumps(players), hash_value)
        )
        conn.commit()
        print(f"Inserted new team: {team_name} for game: {game}")
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        print(f"Team {team_name} already exists for game {game}. Use update instead.")
        return None
    except Exception as e:
        print(f"Error inserting EWC team player data: {e}")
        return None
    finally:
        conn.close()

def get_ewc_team_player_data(game, team_name):
    """Get specific EWC team player data by game and team name"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT * FROM ewc_teams_players 
               WHERE game = ? AND team_name = ? 
               ORDER BY updated_at DESC LIMIT 1""",
            (game, team_name)
        )
        row = cursor.fetchone()
        if row:
            data = dict(row)
            # Parse JSON string back to Python object
            try:
                data['players'] = json.loads(data['players']) if data['players'] else []
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON in players field for {team_name}")
                data['players'] = []
            return data
        return None
    except Exception as e:
        print(f"Error retrieving EWC team player data: {e}")
        return None
    finally:
        conn.close()

def update_ewc_team_player_data(game, team_name, placement, tournament, tournament_logo, years, players, hash_value):
    """Update existing EWC team player data"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE ewc_teams_players 
               SET placement = ?, tournament = ?, tournament_logo = ?, years = ?, 
                   players = ?, hash_value = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE game = ? AND team_name = ?""",
            (placement, tournament, tournament_logo, years, json.dumps(players), hash_value, game, team_name)
        )
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Updated team: {team_name} for game: {game}")
            return True
        else:
            print(f"No team found to update: {team_name} for game: {game}")
            return False
    except Exception as e:
        print(f"Error updating EWC team player data: {e}")
        return False
    finally:
        conn.close()

def get_all_ewc_team_player_data(game):
    """Get all EWC team player data for a specific game"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT * FROM ewc_teams_players 
               WHERE game = ? 
               ORDER BY updated_at DESC""",
            (game,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            data = dict(row)
            # Parse JSON string back to Python object
            try:
                data['players'] = json.loads(data['players']) if data['players'] else []
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON in players field for {data.get('team_name', 'unknown')}")
                data['players'] = []
            result.append(data)
        print(f"Retrieved {len(result)} teams for game: {game}")
        return result
    except Exception as e:
        print(f"Error retrieving all EWC team player data: {e}")
        return []
    finally:
        conn.close()

def upsert_ewc_team_player_data(game, team_name, placement, tournament, tournament_logo, years, players, hash_value):
    """Insert or update EWC team player data (upsert operation)"""
    existing_data = get_ewc_team_player_data(game, team_name)
    
    if existing_data:
        # Update existing record
        return update_ewc_team_player_data(game, team_name, placement, tournament, tournament_logo, years, players, hash_value)
    else:
        # Insert new record
        result = insert_ewc_team_player_data(game, team_name, placement, tournament, tournament_logo, years, players, hash_value)
        return result is not None

def delete_ewc_team_player_data(game, team_name=None):
    """Delete EWC team player data. If team_name is None, delete all data for the game."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if team_name:
            cursor.execute(
                "DELETE FROM ewc_teams_players WHERE game = ? AND team_name = ?",
                (game, team_name)
            )
            print(f"Deleted team: {team_name} for game: {game}")
        else:
            cursor.execute(
                "DELETE FROM ewc_teams_players WHERE game = ?",
                (game,)
            )
            print(f"Deleted all teams for game: {game}")
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting EWC team player data: {e}")
        return False
    finally:
        conn.close()