import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib
import os
import logging
from .db import get_connection

logger = logging.getLogger(__name__)

BASE_URL = 'https://liquipedia.net'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def get_main_page_html_via_api(game_name):
    """
    Get the HTML content for the main page using MediaWiki API (prop=text).
    """
    api_url = f"{BASE_URL}/{game_name}/api.php"
    params = {
        "action": "parse",
        "page": "Main_Page",
        "format": "json",
        "prop": "text"
    }
    try:
        response = requests.get(api_url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("parse", {}).get("text", {}).get("*", "")
    except Exception as e:
        logger.error(f"API fetch failed: {e}")
    return None

def calculate_hash(text):
    """Calculate MD5 hash of text"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def parse_transfer_html(html):
    """Parse transfer HTML and extract transfer data"""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one('div.divTable.mainpage-transfer.Ref')
    if not table:
        logger.error("No transfer table found in HTML.")
        return []

    data = []
    for row in table.select('div.divRow'):
        try:
            date = row.select_one('div.Date')
            date = date.text.strip() if date else 'N/A'

            players = []
            for block in row.select('div.Name .block-player'):
                name_tag = block.select_one('.name a')
                name = name_tag.text.strip() if name_tag else "N/A"
                flag = block.select_one('img')
                flag_url = BASE_URL + flag['src'] if flag else None
                players.append({
                    "Name": name,
                    "Flag": flag_url
                })

            old_light = row.select_one('div.OldTeam .team-template-lightmode img')
            old_dark = row.select_one('div.OldTeam .team-template-darkmode img')
            old_name = old_light['alt'] if old_light else (old_dark['alt'] if old_dark else "None")
            old_logo_light = BASE_URL + old_light['src'] if old_light else None
            old_logo_dark = BASE_URL + old_dark['src'] if old_dark else None

            new_light = row.select_one('div.NewTeam .team-template-lightmode img')
            new_dark = row.select_one('div.NewTeam .team-template-darkmode img')
            new_name = new_light['alt'] if new_light else (new_dark['alt'] if new_dark else "None")
            new_logo_light = BASE_URL + new_light['src'] if new_light else None
            new_logo_dark = BASE_URL + new_dark['src'] if new_dark else None

            unique_id = f"{date}_{players[0]['Name'] if players else 'unknown'}"

            data.append({
                "Date": date,
                "Players": players,
                "OldTeam": {
                    "Name": old_name,
                    "Logo_Light": old_logo_light,
                    "Logo_Dark": old_logo_dark
                },
                "NewTeam": {
                    "Name": new_name,
                    "Logo_Light": new_logo_light,
                    "Logo_Dark": new_logo_dark
                },
                "Unique_ID": unique_id
            })
        except Exception as e:
            logger.error(f"Failed to parse row: {e}")
            continue
    return data

def store_transfers_in_db(game: str, transfers_data: list, hash_value: str):
    """
    Store transfers data in the transfers table
    Note: Each transfer entry can have multiple players, so we create one row per player
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing transfers for this game
        cursor.execute("DELETE FROM transfers WHERE game = ?", (game,))
        
        # Insert new transfers
        for transfer in transfers_data:
            date = transfer.get('Date', '')
            old_team = transfer.get('OldTeam', {})
            new_team = transfer.get('NewTeam', {})
            players = transfer.get('Players', [])
            
            # Create one row per player in the transfer
            for i, player in enumerate(players):
                # Create unique ID for each player in the transfer
                unique_id = f"{date}_{player.get('Name', 'unknown')}_{i}"
                
                cursor.execute("""
                    INSERT INTO transfers (
                        unique_id, game, date, player_name, player_flag,
                        old_team_name, old_team_logo_light, old_team_logo_dark,
                        new_team_name, new_team_logo_light, new_team_logo_dark,
                        hash_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    unique_id,
                    game,
                    date,
                    player.get('Name', ''),
                    player.get('Flag', ''),
                    old_team.get('Name', ''),
                    old_team.get('Logo_Light', ''),
                    old_team.get('Logo_Dark', ''),
                    new_team.get('Name', ''),
                    new_team.get('Logo_Light', ''),
                    new_team.get('Logo_Dark', ''),
                    hash_value
                ))
        
        conn.commit()
        logger.info(f"Stored transfers for {game}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing transfers: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_data_file(game_name):
    """
    Update data file with new transfers (file-based approach)
    """
    filename = f"{game_name.lower()}_transfers.json"
    hasfile = f"{game_name.lower()}_transfer_hash.txt"

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            old_ids = {entry['Unique_ID'] for entry in old_data}
    except FileNotFoundError:
        old_data = []
        old_ids = set()

    html = get_main_page_html_via_api(game_name)
    if not html:
        logger.error("Failed to get HTML from API.")
        return

    current_hash = calculate_hash(html)
    if os.path.exists(hasfile):
        with open(hasfile, 'r', encoding='utf-8') as f:
            old_hash = f.read().strip()
        if current_hash == old_hash:
            logger.info("No changes detected. Skipping update.")
            return

    new_data = parse_transfer_html(html)
    added = 0
    for entry in new_data:
        if entry['Unique_ID'] not in old_ids:
            old_data.append(entry)
            added += 1

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(old_data, f, ensure_ascii=False, indent=2)

    with open(hasfile, 'w', encoding='utf-8') as f:
        f.write(current_hash)

    logger.info(f"Updated '{filename}' - New transfers added: {added}")

def fetch_and_store_transfers(game: str):
    """
    Fetch transfers and store them in database if changed
    """
    html = get_main_page_html_via_api(game)
    if not html:
        logger.error(f"Failed to get HTML for {game}")
        return {"status": "error", "message": "Failed to fetch transfer data"}
    
    # Calculate hash of the HTML content
    new_hash = calculate_hash(html)
    
    # Check if data has changed
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT hash_value FROM transfers 
        WHERE game = ? 
        LIMIT 1
    """, (game,))
    
    existing_hash = cursor.fetchone()
    conn.close()
    
    if existing_hash and existing_hash[0] == new_hash:
        logger.info(f"{game}: no changes detected")
        return {"status": "no_changes", "message": "No changes detected"}
    
    # Parse new data
    transfers_data = parse_transfer_html(html)
    if not transfers_data:
        logger.warning(f"{game}: no transfers found")
        return {"status": "no_transfers", "message": "No transfers found"}
    
    # Store new data
    if store_transfers_in_db(game, transfers_data, new_hash):
        transfer_count = sum(len(transfer.get('Players', [])) for transfer in transfers_data)
        logger.info(f"{game}: {transfer_count} player transfers stored")
        return {
            "status": "updated", 
            "message": f"{transfer_count} player transfers stored successfully",
            "transfer_count": transfer_count
        }
    else:
        return {"status": "error", "message": "Failed to store transfers"}

def get_transfers_from_db(game=None, player_name=None, old_team=None, new_team=None, 
                         date_from=None, date_to=None, page=1, per_page=20, 
                         sort_by='date', sort_order='desc'):
    """
    Retrieve transfers from database with filters and pagination
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build WHERE clause
    where_conditions = []
    params = []
    
    if game:
        where_conditions.append("game = ?")
        params.append(game)
    
    if player_name:
        where_conditions.append("player_name LIKE ?")
        params.append(f"%{player_name}%")
    
    if old_team:
        where_conditions.append("old_team_name LIKE ?")
        params.append(f"%{old_team}%")
    
    if new_team:
        where_conditions.append("new_team_name LIKE ?")
        params.append(f"%{new_team}%")
    
    if date_from:
        where_conditions.append("date >= ?")
        params.append(date_from)
    
    if date_to:
        where_conditions.append("date <= ?")
        params.append(date_to)
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    # Validate sort parameters
    valid_sort_columns = ['date', 'player_name', 'old_team_name', 'new_team_name', 'created_at']
    if sort_by not in valid_sort_columns:
        sort_by = 'date'
    
    if sort_order.lower() not in ['asc', 'desc']:
        sort_order = 'desc'
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM transfers WHERE {where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    # Calculate pagination
    offset = (page - 1) * per_page
    total_pages = (total_count + per_page - 1) // per_page
    
    # Get transfers with pagination
    query = f"""
        SELECT * FROM transfers 
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_order.upper()}, id {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    
    cursor.execute(query, params + [per_page, offset])
    transfers = cursor.fetchall()
    
    conn.close()
    
    # Convert to list of dictionaries
    transfers_list = []
    for transfer in transfers:
        transfers_list.append({
            'id': transfer['id'],
            'unique_id': transfer['unique_id'],
            'game': transfer['game'],
            'date': transfer['date'],
            'player': {
                'name': transfer['player_name'],
                'flag': transfer['player_flag']
            },
            'old_team': {
                'name': transfer['old_team_name'],
                'logo_light': transfer['old_team_logo_light'],
                'logo_dark': transfer['old_team_logo_dark']
            },
            'new_team': {
                'name': transfer['new_team_name'],
                'logo_light': transfer['new_team_logo_light'],
                'logo_dark': transfer['new_team_logo_dark']
            },
            'created_at': transfer['created_at'],
            'updated_at': transfer['updated_at']
        })
    
    return {
        'transfers': transfers_list,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

def get_available_transfer_games():
    """Get list of available games from the transfers table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT game FROM transfers ORDER BY game")
    games = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return games

def get_available_teams(game=None):
    """Get list of available teams (both old and new), optionally filtered by game"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if game:
        cursor.execute("""
            SELECT DISTINCT team_name FROM (
                SELECT old_team_name as team_name FROM transfers WHERE game = ? AND old_team_name != 'None'
                UNION
                SELECT new_team_name as team_name FROM transfers WHERE game = ? AND new_team_name != 'None'
            ) ORDER BY team_name
        """, (game, game))
    else:
        cursor.execute("""
            SELECT DISTINCT team_name FROM (
                SELECT old_team_name as team_name FROM transfers WHERE old_team_name != 'None'
                UNION
                SELECT new_team_name as team_name FROM transfers WHERE new_team_name != 'None'
            ) ORDER BY team_name
        """)
    
    teams = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return teams

def get_available_players(game=None):
    """Get list of available players, optionally filtered by game"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if game:
        cursor.execute("SELECT DISTINCT player_name FROM transfers WHERE game = ? ORDER BY player_name", (game,))
    else:
        cursor.execute("SELECT DISTINCT player_name FROM transfers ORDER BY player_name")
    
    players = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return players

def delete_transfers(game=None):
    """Delete transfers from database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if game:
            cursor.execute("DELETE FROM transfers WHERE game = ?", (game,))
        else:
            cursor.execute("DELETE FROM transfers")
        
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"Deleted {deleted_count} transfers")
        return {"status": "success", "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Error deleting transfers: {str(e)}")
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

def import_transfers_from_json(game: str, json_data: list):
    """
    Import transfers from JSON data (for bulk import)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing transfers for this game
        cursor.execute("DELETE FROM transfers WHERE game = ?", (game,))
        
        # Insert transfers from JSON
        for transfer in json_data:
            date = transfer.get('Date', '')
            old_team = transfer.get('OldTeam', {})
            new_team = transfer.get('NewTeam', {})
            players = transfer.get('Players', [])
            
            # Create one row per player in the transfer
            for i, player in enumerate(players):
                # Create unique ID for each player in the transfer
                unique_id = f"{date}_{player.get('Name', 'unknown')}_{i}"
                
                cursor.execute("""
                    INSERT INTO transfers (
                        unique_id, game, date, player_name, player_flag,
                        old_team_name, old_team_logo_light, old_team_logo_dark,
                        new_team_name, new_team_logo_light, new_team_logo_dark
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    unique_id,
                    game,
                    date,
                    player.get('Name', ''),
                    player.get('Flag', ''),
                    old_team.get('Name', ''),
                    old_team.get('Logo_Light', ''),
                    old_team.get('Logo_Dark', ''),
                    new_team.get('Name', ''),
                    new_team.get('Logo_Light', ''),
                    new_team.get('Logo_Dark', '')
                ))
        
        conn.commit()
        transfer_count = sum(len(transfer.get('Players', [])) for transfer in json_data)
        logger.info(f"Imported {transfer_count} transfers for {game}")
        return {
            "status": "success", 
            "message": f"{transfer_count} transfers imported successfully",
            "transfer_count": transfer_count
        }
        
    except Exception as e:
        logger.error(f"Error importing transfers: {str(e)}")
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()