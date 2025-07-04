import sqlite3
import logging
from .db import get_connection

logger = logging.getLogger(__name__)

def fts_search_news(query, page=1, per_page=10):
    """Full-text search in news using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Prepare FTS query - escape special characters
        fts_query = query.replace('"', '""')
        
        # Count total results
        cursor.execute('''
            SELECT COUNT(*) FROM news_fts 
            WHERE news_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        # Get paginated results with ranking
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT n.*, rank
            FROM news_fts 
            JOIN news n ON news_fts.rowid = n.id
            WHERE news_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in news: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_teams(query, page=1, per_page=10):
    """Full-text search in teams using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM teams_fts 
            WHERE teams_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT t.*, rank
            FROM teams_fts 
            JOIN teams t ON teams_fts.rowid = t.id
            WHERE teams_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in teams: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_events(query, page=1, per_page=10):
    """Full-text search in events using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM events_fts 
            WHERE events_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT e.*, rank
            FROM events_fts 
            JOIN events e ON events_fts.rowid = e.id
            WHERE events_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in events: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_games(query, page=1, per_page=10):
    """Full-text search in games using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM games_fts 
            WHERE games_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT g.*, rank
            FROM games_fts 
            JOIN games g ON games_fts.rowid = g.id
            WHERE games_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in games: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_matches(query, page=1, per_page=10):
    """Full-text search in matches using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM matches_fts 
            WHERE matches_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT m.*, rank
            FROM matches_fts 
            JOIN matches m ON matches_fts.rowid = m.id
            WHERE matches_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in matches: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_prize_distribution(query, page=1, per_page=10):
    """Full-text search in prize_distribution using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM prize_distribution_fts 
            WHERE prize_distribution_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT p.*, rank
            FROM prize_distribution_fts 
            JOIN prize_distribution p ON prize_distribution_fts.rowid = p.id
            WHERE prize_distribution_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in prize_distribution: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_ewc_info(query, page=1, per_page=10):
    """Full-text search in ewc_info using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM ewc_info_fts 
            WHERE ewc_info_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT e.*, rank
            FROM ewc_info_fts 
            JOIN ewc_info e ON ewc_info_fts.rowid = e.id
            WHERE ewc_info_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in ewc_info: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_group_matches(query, page=1, per_page=10):
    """Full-text search in group_matches using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM group_matches_fts 
            WHERE group_matches_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT g.*, rank
            FROM group_matches_fts 
            JOIN group_matches g ON group_matches_fts.rowid = g.id
            WHERE group_matches_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in group_matches: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_transfers(query, page=1, per_page=10):
    """Full-text search in transfers using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM transfers_fts 
            WHERE transfers_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT t.*, rank
            FROM transfers_fts 
            JOIN transfers t ON transfers_fts.rowid = t.id
            WHERE transfers_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in transfers: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_global_matches(query, page=1, per_page=10):
    """Full-text search in global_matches using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM global_matches_fts 
            WHERE global_matches_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT g.*, rank
            FROM global_matches_fts 
            JOIN global_matches g ON global_matches_fts.rowid = g.id
            WHERE global_matches_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in global_matches: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_ewc_teams_players(query, page=1, per_page=10):
    """Full-text search in ewc_teams_players using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM ewc_teams_players_fts 
            WHERE ewc_teams_players_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT e.*, rank
            FROM ewc_teams_players_fts 
            JOIN ewc_teams_players e ON ewc_teams_players_fts.rowid = e.id
            WHERE ewc_teams_players_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in ewc_teams_players: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_player_information(query, page=1, per_page=10):
    """Full-text search in player_information using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM player_information_fts 
            WHERE player_information_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT p.*, rank
            FROM player_information_fts 
            JOIN player_information p ON player_information_fts.rowid = p.id
            WHERE player_information_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in player_information: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_search_team_information(query, page=1, per_page=10):
    """Full-text search in team_information using FTS5"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        fts_query = query.replace('"', '""')
        
        cursor.execute('''
            SELECT COUNT(*) FROM team_information_fts 
            WHERE team_information_fts MATCH ?
        ''', (fts_query,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT t.*, rank
            FROM team_information_fts 
            JOIN team_information t ON team_information_fts.rowid = t.id
            WHERE team_information_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        ''', (fts_query, per_page, offset))
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"FTS search error in team_information: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fts_global_search(query, page=1, per_page=10):
    """Perform FTS search across all tables"""
    results = {}
    total_count = 0
    
    # Search each table type
    search_functions = {
        'news': fts_search_news,
        'teams': fts_search_teams,
        'events': fts_search_events,
        'games': fts_search_games,
        'matches': fts_search_matches,
        'prize_distribution': fts_search_prize_distribution,
        'ewc_info': fts_search_ewc_info,
        'group_matches': fts_search_group_matches,
        'transfers': fts_search_transfers,
        'global_matches': fts_search_global_matches,
        'ewc_teams_players': fts_search_ewc_teams_players,
        'player_information': fts_search_player_information,
        'team_information': fts_search_team_information
    }
    
    # Calculate per-table pagination
    per_table = max(1, per_page // len(search_functions))
    
    for table_name, search_func in search_functions.items():
        try:
            table_results, table_total = search_func(query, 1, per_table)
            results[table_name] = table_results
            total_count += table_total
        except Exception as e:
            logger.error(f"Error searching {table_name}: {str(e)}")
            results[table_name] = []
    
    return results, total_count

def rebuild_fts_indexes():
    """Rebuild FTS indexes from existing data"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # List of all FTS tables
        fts_tables = [
            'news_fts', 'teams_fts', 'events_fts', 'games_fts', 'matches_fts',
            'prize_distribution_fts', 'ewc_info_fts', 'group_matches_fts',
            'transfers_fts', 'global_matches_fts', 'ewc_teams_players_fts',
            'player_information_fts', 'team_information_fts'
        ]
        
        for fts_table in fts_tables:
            try:
                cursor.execute(f'INSERT INTO {fts_table}({fts_table}) VALUES("rebuild")')
            except sqlite3.Error as e:
                logger.warning(f"Could not rebuild {fts_table}: {str(e)}")
        
        conn.commit()
        logger.info("FTS indexes rebuilt successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Error rebuilding FTS indexes: {str(e)}")
        raise
    finally:
        conn.close()

def populate_fts_tables():
    """Populate FTS tables with existing data"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Populate news FTS
        try:
            cursor.execute('''
                INSERT INTO news_fts(rowid, title, description, writer)
                SELECT id, title, description, writer FROM news
            ''')
        except sqlite3.Error:
            pass  # Table might already be populated
        
        # Populate teams FTS
        try:
            cursor.execute('''
                INSERT INTO teams_fts(rowid, team_name)
                SELECT id, team_name FROM teams
            ''')
        except sqlite3.Error:
            pass
        
        # Populate events FTS
        try:
            cursor.execute('''
                INSERT INTO events_fts(rowid, name)
                SELECT id, name FROM events
            ''')
        except sqlite3.Error:
            pass
        
        # Populate games FTS
        try:
            cursor.execute('''
                INSERT INTO games_fts(rowid, game_name, genre, platform, description)
                SELECT id, game_name, genre, platform, description FROM games
            ''')
        except sqlite3.Error:
            pass
        
        # Populate matches FTS
        try:
            cursor.execute('''
                INSERT INTO matches_fts(rowid, game, group_name, team1_name, team2_name)
                SELECT id, game, group_name, team1_name, team2_name FROM matches
            ''')
        except sqlite3.Error:
            pass
        
        # Populate prize_distribution FTS
        try:
            cursor.execute('''
                INSERT INTO prize_distribution_fts(rowid, place, prize, participants)
                SELECT id, place, prize, participants FROM prize_distribution
            ''')
        except sqlite3.Error:
            pass
        
        # Populate ewc_info FTS
        try:
            cursor.execute('''
                INSERT INTO ewc_info_fts(rowid, header, series, organizers, location, prize_pool, liquipedia_tier)
                SELECT id, header, series, organizers, location, prize_pool, liquipedia_tier FROM ewc_info
            ''')
        except sqlite3.Error:
            pass
        
        # Populate transfers FTS
        try:
            cursor.execute('''
                INSERT INTO transfers_fts(rowid, game, player_name, old_team_name, new_team_name)
                SELECT id, game, player_name, old_team_name, new_team_name FROM transfers
            ''')
        except sqlite3.Error:
            pass
        
        # Populate ewc_teams_players FTS
        try:
            cursor.execute('''
                INSERT INTO ewc_teams_players_fts(rowid, game, team_name, placement, tournament, players)
                SELECT id, game, team_name, placement, tournament, players FROM ewc_teams_players
            ''')
        except sqlite3.Error:
            pass
        
        # Populate player_information FTS
        try:
            cursor.execute('''
                INSERT INTO player_information_fts(rowid, game, player_page_name, data)
                SELECT id, game, player_page_name, data FROM player_information
            ''')
        except sqlite3.Error:
            pass
        
        # Populate team_information FTS
        try:
            cursor.execute('''
                INSERT INTO team_information_fts(rowid, game, team_page_name, data)
                SELECT id, game, team_page_name, data FROM team_information
            ''')
        except sqlite3.Error:
            pass
        
        conn.commit()
        logger.info("FTS tables populated successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Error populating FTS tables: {str(e)}")
        # This might fail if tables are already populated, which is okay
        pass
    finally:
        conn.close()

