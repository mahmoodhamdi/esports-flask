import requests
from bs4 import BeautifulSoup
import json
import hashlib
import logging
from datetime import datetime
from .db import get_connection
from .utils import get_html_via_api, extract_matches_from_html

logger = logging.getLogger(__name__)

def calculate_hash(text):
    """Calculate MD5 hash of text"""
    return hashlib.md5(text.encode()).hexdigest()

def fetch_group_stage_matches(game: str, tournament: str):
    """
    Fetch group stage matches for a specific game and tournament
    Similar to fixtures.py but returns structured data
    """
    page = f"{tournament}/Group_Stage"
    html = get_html_via_api(game, page)
    
    if html is None or html.strip() == "":
        page = tournament
        html = get_html_via_api(game, page)
        if html is None or html.strip() == "":
            return {"status": "missing_page", "matches": None}
        
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.find(lambda tag: tag.name in ['span','h2','h3'] and 'Group Stage' in tag.text)
        if header:
            sec = header.find_next('div', class_='brkts-matchlist-container')
            if sec:
                matches = extract_matches_from_html(str(sec))
                return {"status": "ok", "matches": matches, "html": str(sec)}
        return {"status": "no_matches", "matches": None}
    
    matches = extract_matches_from_html(html)
    if not matches:
        return {"status": "no_matches", "matches": None}
    
    return {"status": "ok", "matches": matches, "html": html}

def store_matches_in_db(game: str, tournament: str, matches_data: dict, hash_value: str):
    """
    Store matches data in the global_matches table
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing matches for this game and tournament
        cursor.execute("""
            DELETE FROM global_matches 
            WHERE game = ? AND tournament = ?
        """, (game, tournament))
        
        # Insert new matches
        for group_name, matches in matches_data.items():
            for match in matches:
                cursor.execute("""
                    INSERT INTO global_matches (
                        game, tournament, group_name, team1_name, team1_logo,
                        team2_name, team2_logo, match_time, score, hash_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    game,
                    tournament,
                    group_name,
                    match.get('Team1', {}).get('Name', ''),
                    match.get('Team1', {}).get('Logo', ''),
                    match.get('Team2', {}).get('Name', ''),
                    match.get('Team2', {}).get('Logo', ''),
                    match.get('MatchTime', ''),
                    match.get('Score', 'N/A'),
                    hash_value
                ))
        
        conn.commit()
        logger.info(f"Stored matches for {game} - {tournament}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing matches: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def fetch_and_store_matches(game: str, tournament: str):
    """
    Fetch matches and store them in database if changed
    """
    result = fetch_group_stage_matches(game, tournament)
    status = result["status"]
    
    if status in ("missing_page", "no_matches"):
        logger.info(f"{game} - {tournament}: {status}")
        return {"status": status, "message": "Matches have not been added yet."}
    
    # Calculate hash of the HTML content
    html_content = result.get("html", "")
    new_hash = calculate_hash(html_content)
    
    # Check if data has changed
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT hash_value FROM global_matches 
        WHERE game = ? AND tournament = ? 
        LIMIT 1
    """, (game, tournament))
    
    existing_hash = cursor.fetchone()
    conn.close()
    
    if existing_hash and existing_hash[0] == new_hash:
        logger.info(f"{game} - {tournament}: no changes detected")
        return {"status": "no_changes", "message": "No changes detected"}
    
    # Store new data
    if store_matches_in_db(game, tournament, result["matches"], new_hash):
        match_count = sum(len(matches) for matches in result["matches"].values())
        logger.info(f"{game} - {tournament}: {match_count} matches stored")
        return {
            "status": "updated", 
            "message": f"{match_count} matches stored successfully",
            "match_count": match_count
        }
    else:
        return {"status": "error", "message": "Failed to store matches"}

def get_matches_from_db(game=None, tournament=None, group_name=None, team=None, 
                       page=1, per_page=20, sort_by='match_time', sort_order='asc'):
    """
    Retrieve matches from database with filters and pagination
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build WHERE clause
    where_conditions = []
    params = []
    
    if game:
        where_conditions.append("game = ?")
        params.append(game)
    
    if tournament:
        where_conditions.append("tournament = ?")
        params.append(tournament)
    
    if group_name:
        where_conditions.append("group_name = ?")
        params.append(group_name)
    
    if team:
        where_conditions.append("(team1_name LIKE ? OR team2_name LIKE ?)")
        params.extend([f"%{team}%", f"%{team}%"])
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    # Validate sort parameters
    valid_sort_columns = ['match_time', 'game', 'tournament', 'group_name', 'created_at']
    if sort_by not in valid_sort_columns:
        sort_by = 'match_time'
    
    if sort_order.lower() not in ['asc', 'desc']:
        sort_order = 'asc'
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM global_matches WHERE {where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    # Calculate pagination
    offset = (page - 1) * per_page
    total_pages = (total_count + per_page - 1) // per_page
    
    # Get matches with pagination
    query = f"""
        SELECT * FROM global_matches 
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    
    cursor.execute(query, params + [per_page, offset])
    matches = cursor.fetchall()
    
    conn.close()
    
    # Convert to list of dictionaries
    matches_list = []
    for match in matches:
        matches_list.append({
            'id': match['id'],
            'game': match['game'],
            'tournament': match['tournament'],
            'group_name': match['group_name'],
            'team1': {
                'name': match['team1_name'],
                'logo': match['team1_logo']
            },
            'team2': {
                'name': match['team2_name'],
                'logo': match['team2_logo']
            },
            'match_time': match['match_time'],
            'score': match['score'],
            'status': match['status'],
            'created_at': match['created_at'],
            'updated_at': match['updated_at']
        })
    
    return {
        'matches': matches_list,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

def get_available_games():
    """Get list of available games from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT game FROM global_matches ORDER BY game")
    games = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return games

def get_available_tournaments(game=None):
    """Get list of available tournaments, optionally filtered by game"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if game:
        cursor.execute("SELECT DISTINCT tournament FROM global_matches WHERE game = ? ORDER BY tournament", (game,))
    else:
        cursor.execute("SELECT DISTINCT tournament FROM global_matches ORDER BY tournament")
    
    tournaments = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tournaments

def get_available_groups(game=None, tournament=None):
    """Get list of available groups, optionally filtered by game and tournament"""
    conn = get_connection()
    cursor = conn.cursor()
    
    where_conditions = []
    params = []
    
    if game:
        where_conditions.append("game = ?")
        params.append(game)
    
    if tournament:
        where_conditions.append("tournament = ?")
        params.append(tournament)
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    cursor.execute(f"SELECT DISTINCT group_name FROM global_matches WHERE {where_clause} ORDER BY group_name", params)
    groups = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return groups

def delete_matches(game=None, tournament=None):
    """Delete matches from database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if game and tournament:
            cursor.execute("DELETE FROM global_matches WHERE game = ? AND tournament = ?", (game, tournament))
        elif game:
            cursor.execute("DELETE FROM global_matches WHERE game = ?", (game,))
        else:
            cursor.execute("DELETE FROM global_matches")
        
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted_count} matches")
        return {"status": "success", "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Error deleting matches: {str(e)}")
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

