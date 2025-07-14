from app.db import get_connection
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def update_teams_in_db(teams):
    """
    Update the database with teams and their games from teams_ewc.json.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for team in teams:
            logger.debug(f"Processing team: {team['name']}")
            # Insert or update team
            cursor.execute("""
                INSERT INTO new_teams (name, logo_url)
                VALUES (?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    logo_url = excluded.logo_url,
                    updated_at = CURRENT_TIMESTAMP
            """, (team['name'], team['logo_url']))
            team_id = cursor.execute("SELECT id FROM new_teams WHERE name = ?", (team['name'],)).fetchone()[0]
            logger.debug(f"Team {team['name']} assigned ID: {team_id}")
            
            # Clear existing games for this team
            cursor.execute("DELETE FROM team_games WHERE team_id = ?", (team_id,))
            logger.debug(f"Cleared existing games for team_id: {team_id}")
            
            # Insert games and logos
            for game in team.get('games', []):
                if not game.get('game_name'):
                    logger.warning(f"Skipping game with no name for team {team['name']}")
                    continue
                # Insert game with logos
                for logo in game.get('game_logos', []):
                    if not logo.get('mode') or not logo.get('url'):
                        logger.debug(f"Skipping invalid logo for game {game['game_name']} in team {team['name']}")
                        continue
                    cursor.execute("""
                        INSERT INTO team_games (team_id, game_name, logo_mode, logo_url)
                        VALUES (?, ?, ?, ?)
                    """, (team_id, game['game_name'], logo['mode'], logo['url']))
                    logger.debug(f"Inserted game {game['game_name']} with logo (mode: {logo['mode']}) for team_id: {team_id}")
                # Insert game even if no logos (to ensure game_name appears)
                if not game.get('game_logos'):
                    cursor.execute("""
                        INSERT INTO team_games (team_id, game_name, logo_mode, logo_url)
                        VALUES (?, ?, NULL, NULL)
                    """, (team_id, game['game_name']))
                    logger.debug(f"Inserted game {game['game_name']} without logos for team_id: {team_id}")
        
        conn.commit()
        logger.info(f"Successfully updated {len(teams)} teams in database")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error in update_teams_in_db: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error in update_teams_in_db: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_teams(name_filter=None, game_filter=None, page=1, per_page=10):
    """
    Fetch teams with their games from the database, with optional filtering and pagination.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        offset = (page - 1) * per_page
        query = """
            SELECT DISTINCT t.id, t.name, t.logo_url, t.created_at, t.updated_at
            FROM new_teams t
            LEFT JOIN team_games g ON t.id = g.team_id
        """
        params = []
        conditions = []
        if name_filter:
            conditions.append("t.name LIKE ?")
            params.append(f"%{name_filter}%")
        if game_filter:
            conditions.append("g.game_name LIKE ?")
            params.append(f"%{game_filter}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY t.name ASC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        logger.debug(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        teams = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Fetch games for each team
        for team in teams:
            cursor.execute("""
                SELECT game_name, logo_mode, logo_url
                FROM team_games
                WHERE team_id = ?
                ORDER BY game_name
            """, (team['id'],))
            games = {}
            for row in cursor.fetchall():
                game_name, logo_mode, logo_url = row
                if game_name not in games:
                    games[game_name] = {'game_name': game_name, 'game_logos': []}
                if logo_mode and logo_url:
                    games[game_name]['game_logos'].append({'mode': logo_mode, 'url': logo_url})
            team['games'] = [game for game in games.values() if game['game_name']]
            logger.debug(f"Fetched {len(team['games'])} games for team {team['name']}")
        
        count_query = "SELECT COUNT(DISTINCT t.id) FROM new_teams t"
        if game_filter:
            count_query += " LEFT JOIN team_games g ON t.id = g.team_id"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
        cursor.execute(count_query, params[:-2] if params[:-2] else [])
        total = cursor.fetchone()[0]
        logger.debug(f"Total teams matching query: {total}")
        
        return {
            "teams": teams,
            "total": total,
            "page": page,
            "per_page": per_page
        }
    except sqlite3.Error as e:
        logger.error(f"Database error in get_teams: {e}")
        return {"teams": [], "total": 0, "page": page, "per_page": per_page}
    except Exception as e:
        logger.error(f"Unexpected error in get_teams: {e}")
        return {"teams": [], "total": 0, "page": page, "per_page": per_page}
    finally:
        conn.close()