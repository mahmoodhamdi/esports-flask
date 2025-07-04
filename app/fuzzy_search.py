import sqlite3
import logging
from fuzzywuzzy import fuzz, process
from .db import get_connection

logger = logging.getLogger(__name__)

def get_searchable_terms(table_name, field_name):
    """Get all searchable terms from a specific table and field"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT DISTINCT {field_name} FROM {table_name} WHERE {field_name} IS NOT NULL')
        terms = [row[0] for row in cursor.fetchall() if row[0]]
        return terms
        
    except sqlite3.Error as e:
        logger.error(f"Error getting searchable terms: {str(e)}")
        return []
    finally:
        conn.close()

def fuzzy_match_terms(query, terms, threshold=70, limit=5):
    """Find fuzzy matches for a query against a list of terms"""
    if not query or not terms:
        return []
    
    # Use process.extract to get the best matches
    matches = process.extract(query, terms, scorer=fuzz.token_sort_ratio, limit=limit)
    
    # Filter by threshold and return only the terms
    return [match[0] for match in matches if match[1] >= threshold]

def fuzzy_search_news(query, threshold=70, page=1, per_page=10):
    """Fuzzy search in news table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all news titles and descriptions for fuzzy matching
        cursor.execute('SELECT id, title, description FROM news')
        all_news = cursor.fetchall()
        
        # Create searchable text for each news item
        news_texts = {}
        for news_id, title, description in all_news:
            searchable_text = f"{title or ''} {description or ''}".strip()
            if searchable_text:
                news_texts[news_id] = searchable_text
        
        if not news_texts:
            return [], 0
        
        # Find fuzzy matches
        matches = process.extract(query, news_texts.values(), scorer=fuzz.token_sort_ratio, limit=50)
        matched_texts = [match[0] for match in matches if match[1] >= threshold]
        
        if not matched_texts:
            return [], 0
        
        # Get the IDs of matched news items
        matched_ids = []
        for news_id, text in news_texts.items():
            if text in matched_texts:
                matched_ids.append(news_id)
        
        if not matched_ids:
            return [], 0
        
        # Get paginated results
        total = len(matched_ids)
        offset = (page - 1) * per_page
        paginated_ids = matched_ids[offset:offset + per_page]
        
        # Fetch the actual news records
        placeholders = ','.join(['?' for _ in paginated_ids])
        cursor.execute(f'''
            SELECT * FROM news 
            WHERE id IN ({placeholders})
            ORDER BY updated_at DESC
        ''', paginated_ids)
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
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
        
        # Get all team names
        cursor.execute('SELECT team_name FROM teams WHERE team_name IS NOT NULL')
        team_names = [row[0] for row in cursor.fetchall()]
        
        if not team_names:
            return [], 0
        
        # Find fuzzy matches
        matched_names = fuzzy_match_terms(query, team_names, threshold, limit=50)
        
        if not matched_names:
            return [], 0
        
        # Get paginated results
        total = len(matched_names)
        offset = (page - 1) * per_page
        paginated_names = matched_names[offset:offset + per_page]
        
        # Fetch the actual team records
        placeholders = ','.join(['?' for _ in paginated_names])
        cursor.execute(f'''
            SELECT * FROM teams 
            WHERE team_name IN ({placeholders})
            ORDER BY team_name
        ''', paginated_names)
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
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
        
        # Get all event names
        cursor.execute('SELECT name FROM events WHERE name IS NOT NULL')
        event_names = [row[0] for row in cursor.fetchall()]
        
        if not event_names:
            return [], 0
        
        # Find fuzzy matches
        matched_names = fuzzy_match_terms(query, event_names, threshold, limit=50)
        
        if not matched_names:
            return [], 0
        
        # Get paginated results
        total = len(matched_names)
        offset = (page - 1) * per_page
        paginated_names = matched_names[offset:offset + per_page]
        
        # Fetch the actual event records
        placeholders = ','.join(['?' for _ in paginated_names])
        cursor.execute(f'''
            SELECT * FROM events 
            WHERE name IN ({placeholders})
            ORDER BY name
        ''', paginated_names)
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
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
        
        # Get all game data for fuzzy matching
        cursor.execute('SELECT id, game_name, genre, description FROM games')
        all_games = cursor.fetchall()
        
        # Create searchable text for each game
        game_texts = {}
        for game_id, name, genre, description in all_games:
            searchable_text = f"{name or ''} {genre or ''} {description or ''}".strip()
            if searchable_text:
                game_texts[game_id] = searchable_text
        
        if not game_texts:
            return [], 0
        
        # Find fuzzy matches
        matches = process.extract(query, game_texts.values(), scorer=fuzz.token_sort_ratio, limit=50)
        matched_texts = [match[0] for match in matches if match[1] >= threshold]
        
        if not matched_texts:
            return [], 0
        
        # Get the IDs of matched games
        matched_ids = []
        for game_id, text in game_texts.items():
            if text in matched_texts:
                matched_ids.append(game_id)
        
        if not matched_ids:
            return [], 0
        
        # Get paginated results
        total = len(matched_ids)
        offset = (page - 1) * per_page
        paginated_ids = matched_ids[offset:offset + per_page]
        
        # Fetch the actual game records
        placeholders = ','.join(['?' for _ in paginated_ids])
        cursor.execute(f'''
            SELECT * FROM games 
            WHERE id IN ({placeholders})
            ORDER BY game_name
        ''', paginated_ids)
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
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
        
        # Get all match data for fuzzy matching
        cursor.execute('SELECT id, game, team1_name, team2_name, group_name FROM matches')
        all_matches = cursor.fetchall()
        
        # Create searchable text for each match
        match_texts = {}
        for match_id, game, team1, team2, group_name in all_matches:
            searchable_text = f"{game or ''} {team1 or ''} {team2 or ''} {group_name or ''}".strip()
            if searchable_text:
                match_texts[match_id] = searchable_text
        
        if not match_texts:
            return [], 0
        
        # Find fuzzy matches
        matches = process.extract(query, match_texts.values(), scorer=fuzz.token_sort_ratio, limit=50)
        matched_texts = [match[0] for match in matches if match[1] >= threshold]
        
        if not matched_texts:
            return [], 0
        
        # Get the IDs of matched matches
        matched_ids = []
        for match_id, text in match_texts.items():
            if text in matched_texts:
                matched_ids.append(match_id)
        
        if not matched_ids:
            return [], 0
        
        # Get paginated results
        total = len(matched_ids)
        offset = (page - 1) * per_page
        paginated_ids = matched_ids[offset:offset + per_page]
        
        # Fetch the actual match records
        placeholders = ','.join(['?' for _ in paginated_ids])
        cursor.execute(f'''
            SELECT * FROM matches 
            WHERE id IN ({placeholders})
            ORDER BY match_date DESC
        ''', paginated_ids)
        
        results = [dict(row) for row in cursor.fetchall()]
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"Fuzzy search error in matches: {str(e)}")
        return [], 0
    finally:
        conn.close()

def fuzzy_global_search(query, threshold=70, page=1, per_page=10):
    """Perform fuzzy search across all tables"""
    results = {}
    total_count = 0
    
    # Search each table type
    search_functions = {
        'news': fuzzy_search_news,
        'teams': fuzzy_search_teams,
        'events': fuzzy_search_events,
        'games': fuzzy_search_games,
        'matches': fuzzy_search_matches
    }
    
    # Calculate per-table pagination
    per_table = max(1, per_page // len(search_functions))
    
    for table_name, search_func in search_functions.items():
        try:
            table_results, table_total = search_func(query, threshold, 1, per_table)
            results[table_name] = table_results
            total_count += table_total
        except Exception as e:
            logger.error(f"Error in fuzzy search {table_name}: {str(e)}")
            results[table_name] = []
    
    return results, total_count

def suggest_corrections(query, threshold=60):
    """Suggest spelling corrections for a query"""
    suggestions = set()
    
    # Get terms from different tables
    tables_fields = [
        ('news', 'title'),
        ('teams', 'team_name'),
        ('events', 'name'),
        ('games', 'game_name')
    ]
    
    for table, field in tables_fields:
        terms = get_searchable_terms(table, field)
        matches = fuzzy_match_terms(query, terms, threshold, limit=3)
        suggestions.update(matches)
    
    return list(suggestions)[:5]  # Return top 5 suggestions

