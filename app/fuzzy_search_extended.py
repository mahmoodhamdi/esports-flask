import sqlite3
import logging
from fuzzywuzzy import fuzz, process
from .db import get_connection

logger = logging.getLogger(__name__)

def fuzzy_search_news(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in news table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all news records
        cursor.execute('SELECT * FROM news')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        # Perform fuzzy matching on searchable fields
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('title', '')} {record.get('description', '')} {record.get('writer', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        # Sort by fuzzy score (descending)
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        # Apply pagination
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in news: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_teams(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in teams table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM teams')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('team_name', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in teams: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_events(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in events table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM events')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('name', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in events: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_games(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in games table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM games')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('game_name', '')} {record.get('genre', '')} {record.get('platform', '')} {record.get('description', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in games: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_matches(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in matches table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM matches')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('game', '')} {record.get('group_name', '')} {record.get('team1_name', '')} {record.get('team2_name', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in matches: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_prize_distribution(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in prize_distribution table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM prize_distribution')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('place', '')} {record.get('prize', '')} {record.get('participants', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in prize_distribution: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_ewc_info(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in ewc_info table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ewc_info')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('header', '')} {record.get('series', '')} {record.get('organizers', '')} {record.get('location', '')} {record.get('prize_pool', '')} {record.get('liquipedia_tier', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in ewc_info: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_group_matches(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in group_matches table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM group_matches')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('game', '')} {record.get('tournament', '')} {record.get('group_name', '')} {record.get('team1_name', '')} {record.get('team2_name', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in group_matches: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_transfers(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in transfers table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM transfers')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('game', '')} {record.get('player_name', '')} {record.get('old_team_name', '')} {record.get('new_team_name', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in transfers: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_global_matches(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in global_matches table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM global_matches')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('game', '')} {record.get('tournament', '')} {record.get('group_name', '')} {record.get('team1_name', '')} {record.get('team2_name', '')} {record.get('status', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in global_matches: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_ewc_teams_players(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in ewc_teams_players table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ewc_teams_players')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('game', '')} {record.get('team_name', '')} {record.get('placement', '')} {record.get('tournament', '')} {record.get('players', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in ewc_teams_players: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_player_information(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in player_information table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM player_information')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('game', '')} {record.get('player_page_name', '')} {record.get('data', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in player_information: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_search_team_information(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in team_information table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM team_information')
        all_records = [dict(row) for row in cursor.fetchall()]
        
        matches = []
        for record in all_records:
            searchable_text = f"{record.get('game', '')} {record.get('team_page_name', '')} {record.get('data', '')}"
            score = fuzz.partial_ratio(query.lower(), searchable_text.lower())
            
            if score >= threshold:
                record['fuzzy_score'] = score
                matches.append(record)
        
        matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
        
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_matches = matches[start:end]
        
        return paginated_matches, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in team_information: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_global_search_extended(query, threshold=70, page=1, per_page=10):
    """Perform fuzzy search across all tables"""
    results = {}
    total_count = 0
    
    # Search functions for all tables
    search_functions = {
        'news': fuzzy_search_news,
        'teams': fuzzy_search_teams,
        'events': fuzzy_search_events,
        'games': fuzzy_search_games,
        'matches': fuzzy_search_matches,
        'prize_distribution': fuzzy_search_prize_distribution,
        'ewc_info': fuzzy_search_ewc_info,
        'group_matches': fuzzy_search_group_matches,
        'transfers': fuzzy_search_transfers,
        'global_matches': fuzzy_search_global_matches,
        'ewc_teams_players': fuzzy_search_ewc_teams_players,
        'player_information': fuzzy_search_player_information,
        'team_information': fuzzy_search_team_information
    }
    
    # Calculate per-table pagination
    per_table = max(1, per_page // len(search_functions))
    
    for table_name, search_func in search_functions.items():
        try:
            table_results, table_total = search_func(query, threshold, 1, per_table)
            results[table_name] = table_results
            total_count += table_total
        except Exception as e:
            logger.error(f"Error in fuzzy search for {table_name}: {str(e)}")
            results[table_name] = []
    
    return results, total_count

def suggest_corrections_extended(query, threshold=60):
    """Suggest spelling corrections for a query based on existing data from all tables"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Collect searchable terms from all tables
        searchable_terms = set()
        
        # From news
        cursor.execute('SELECT title, writer FROM news')
        for row in cursor.fetchall():
            if row[0]:  # title
                searchable_terms.update(row[0].split())
            if row[1]:  # writer
                searchable_terms.update(row[1].split())
        
        # From teams
        cursor.execute('SELECT team_name FROM teams')
        for row in cursor.fetchall():
            if row[0]:
                searchable_terms.update(row[0].split())
        
        # From events
        cursor.execute('SELECT name FROM events')
        for row in cursor.fetchall():
            if row[0]:
                searchable_terms.update(row[0].split())
        
        # From games
        cursor.execute('SELECT game_name, genre FROM games')
        for row in cursor.fetchall():
            if row[0]:  # game_name
                searchable_terms.update(row[0].split())
            if row[1]:  # genre
                searchable_terms.update(row[1].split())
        
        # From transfers
        cursor.execute('SELECT player_name, old_team_name, new_team_name FROM transfers')
        for row in cursor.fetchall():
            for field in row:
                if field:
                    searchable_terms.update(field.split())
        
        # From ewc_info
        cursor.execute('SELECT header, series, organizers, location FROM ewc_info')
        for row in cursor.fetchall():
            for field in row:
                if field:
                    searchable_terms.update(field.split())
        
        # From ewc_teams_players
        cursor.execute('SELECT team_name, tournament FROM ewc_teams_players')
        for row in cursor.fetchall():
            for field in row:
                if field:
                    searchable_terms.update(field.split())
        
        # Clean and filter terms
        searchable_terms = {term.strip().lower() for term in searchable_terms 
                          if term and len(term) > 2 and term.isalpha()}
        
        # Find best matches using fuzzy matching
        if searchable_terms:
            matches = process.extract(query.lower(), list(searchable_terms), 
                                    scorer=fuzz.ratio, limit=5)
            suggestions = [match[0] for match in matches if match[1] >= threshold]
            return suggestions[:3]  # Return top 3 suggestions
        
        return []
        
    except sqlite3.Error as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        return []
    finally:
        conn.close()

def get_table_field_suggestions_extended(table_name, field_name, query, threshold=60):
    """Get suggestions for a specific table field"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all values from the specified field
        cursor.execute(f'SELECT DISTINCT {field_name} FROM {table_name} WHERE {field_name} IS NOT NULL')
        field_values = [row[0] for row in cursor.fetchall() if row[0]]
        
        if field_values:
            matches = process.extract(query.lower(), 
                                    [val.lower() for val in field_values], 
                                    scorer=fuzz.ratio, limit=5)
            suggestions = [match[0] for match in matches if match[1] >= threshold]
            return suggestions[:3]
        
        return []
        
    except sqlite3.Error as e:
        logger.error(f"Error getting field suggestions: {str(e)}")
        return []
    finally:
        conn.close()

