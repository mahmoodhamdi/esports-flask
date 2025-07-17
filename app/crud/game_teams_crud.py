import json
import os
import sqlite3
import logging
from app.db import get_connection
from app.game_teams import JSON_FILE_PATH

logger = logging.getLogger(__name__)

def parse_and_update_teams():
    """Parse teams from JSON and update the game_teams table, preserving all data."""
    if not os.path.exists(JSON_FILE_PATH):
        logger.error(f"JSON file not found at: {JSON_FILE_PATH}")
        return {"error": f"JSON file not found at: {JSON_FILE_PATH}"}

    try:
        with open(JSON_FILE_PATH, 'r') as f:
            teams_data = json.load(f)
        logger.info(f"Successfully loaded JSON file: {JSON_FILE_PATH}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {"error": f"Invalid JSON format: {str(e)}"}
    except Exception as e:
        logger.error(f"Error reading JSON file: {str(e)}")
        return {"error": f"Error reading JSON file: {str(e)}"}

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data for simplicity
        cursor.execute("DELETE FROM game_teams")
        cursor.execute("DELETE FROM game_teams_fts")
        logger.info("Cleared game_teams and game_teams_fts tables")
        
        total_records = 0
        for team in teams_data:
            team_name = team.get('team_name')
            team_logo_url = team.get('logo_url')
            games = team.get('games', [])
            
            for game in games:
                game_name = game.get('game_name')
                game_url = game.get('game_url')
                game_logos = game.get('game_logos', [])
                
                for logo in game_logos:
                    logo_mode = logo.get('mode')
                    logo_url = logo.get('url')
                    
                    # Validate all fields are present
                    if not all([team_name, team_logo_url, game_name, game_url, logo_mode, logo_url]):
                        logger.warning(f"Missing fields in team: {team_name}, game: {game_name}, logo: {logo_mode}")
                        continue
                    
                    cursor.execute("""
                        INSERT INTO game_teams (team_name, team_logo_url, game_name, game_url, logo_mode, logo_url)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        team_name,
                        team_logo_url,
                        game_name,
                        game_url,
                        logo_mode,
                        logo_url
                    ))
                    total_records += 1
        
        conn.commit()
        logger.info(f"Inserted {total_records} records for {len(teams_data)} teams into game_teams")
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        conn.rollback()
        return {"error": f"Database error: {str(e)}"}
    finally:
        conn.close()
    
    return {"success": True}

def get_teams(page=1, per_page=10, name_filter=None, game_filter=None, logo_mode_filter=None, all_filter=None):
    """Retrieve teams with pagination and filters, preserving all data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    
    # Construct the query with filters
    if all_filter:
        # Use FTS5 for full-text search across all fields
        query = """
            SELECT gt.team_name, gt.team_logo_url, gt.game_name, gt.game_url, gt.logo_mode, gt.logo_url
            FROM game_teams gt
            JOIN game_teams_fts gtf ON gt.id = gtf.rowid
            WHERE gtf MATCH ?
        """
        count_query = """
            SELECT COUNT(DISTINCT gt.team_name)
            FROM game_teams gt
            JOIN game_teams_fts gtf ON gt.id = gtf.rowid
            WHERE gtf MATCH ?
        """
        params = [all_filter]
    else:
        query = """
            SELECT team_name, team_logo_url, game_name, game_url, logo_mode, logo_url
            FROM game_teams
        """
        count_query = "SELECT COUNT(DISTINCT team_name) FROM game_teams"
        params = []
        
        where_clauses = []
        if name_filter:
            where_clauses.append("team_name LIKE ?")
            params.append(f"%{name_filter}%")
        if game_filter:
            where_clauses.append("game_name LIKE ?")
            params.append(f"%{game_filter}%")
        if logo_mode_filter:
            where_clauses.append("logo_mode = ?")
            params.append(logo_mode_filter)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            count_query += " WHERE " + " AND ".join(where_clauses)
    
    try:
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get paginated teams
        query += " LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Group by team_name to match JSON structure
        teams_dict = {}
        for row in rows:
            team_name = row['team_name']
            if team_name not in teams_dict:
                teams_dict[team_name] = {
                    'team_name': team_name,
                    'logo_url': row['team_logo_url'],
                    'games': {}
                }
            game_name = row['game_name']
            if game_name not in teams_dict[team_name]['games']:
                teams_dict[team_name]['games'][game_name] = {
                    'game_name': game_name,
                    'game_url': row['game_url'],
                    'game_logos': []
                }
            teams_dict[team_name]['games'][game_name]['game_logos'].append({
                'mode': row['logo_mode'],
                'url': row['logo_url']
            })
        
        # Convert to list and ensure games are a list
        result = []
        for team in teams_dict.values():
            team['games'] = list(team['games'].values())
            result.append(team)
        
        logger.info(f"Retrieved {len(result)} teams (total: {total}) for page {page}, filters: name={name_filter}, game={game_filter}, logo_mode={logo_mode_filter}, all={all_filter}")
        return result, total
    
    except sqlite3.Error as e:
        logger.error(f"Database query error: {str(e)}")
        return [], 0
    finally:
        conn.close()