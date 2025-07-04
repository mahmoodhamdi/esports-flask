import sqlite3
import logging
import time
import random
from .db import get_connection
from .search_logger import log_search_query
from .fts_search import fts_global_search
from .fuzzy_search_extended import fuzzy_global_search_extended, suggest_corrections_extended

logger = logging.getLogger(__name__)

def get_random_items_from_table(table_name, limit=5):
    """Get random items from a specified table."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY RANDOM() LIMIT ?", (limit,))
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except sqlite3.Error as e:
        logger.error(f"Error getting random items from {table_name}: {str(e)}")
        return []
    finally:
        conn.close()

def enhanced_search_extended(query, search_mode='auto', search_type=None, fuzzy_threshold=70, 
                           page=1, per_page=10, filters=None):
    """
    Enhanced search function that combines FTS, fuzzy search, and pagination for all tables
    
    Args:
        query: Search query string
        search_mode: 'auto', 'fts', 'fuzzy', 'hybrid'
        search_type: Specific table to search or None for all
        fuzzy_threshold: Threshold for fuzzy matching (0-100)
        page: Page number for pagination
        per_page: Results per page
        filters: Additional filters as dict
    """
    start_time = time.time()
    
    try:
        if not query or not query.strip():
            all_tables = get_all_table_names_extended()
            random_results = {}
            for table in all_tables:
                random_results[table] = get_random_items_from_table(table, limit=5)
            
            return {
                'results': random_results,
                'total': sum(len(v) for v in random_results.values()),
                'search_mode': 'random',
                'execution_time': time.time() - start_time,
                'suggestions': []
            }
        
        query = query.strip()
        results = {}
        total = 0
        suggestions = []
        
        if search_mode == 'auto':
            # Try FTS first, fallback to fuzzy if no results
            try:
                if search_type:
                    # Search specific table with FTS
                    from .fts_search import (
                        fts_search_news, fts_search_teams, fts_search_events,
                        fts_search_games, fts_search_matches, fts_search_prize_distribution,
                        fts_search_ewc_info, fts_search_group_matches, fts_search_transfers,
                        fts_search_global_matches, fts_search_ewc_teams_players,
                        fts_search_player_information, fts_search_team_information
                    )
                    
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
                    
                    if search_type in search_functions:
                        table_results, table_total = search_functions[search_type](query, page, per_page)
                        results[search_type] = table_results
                        total = table_total
                else:
                    # Global FTS search
                    results, total = fts_global_search(query, page, per_page)
                
                # If FTS returns no results, try fuzzy search
                if total == 0:
                    if search_type:
                        from .fuzzy_search_extended import (
                            fuzzy_search_news, fuzzy_search_teams, fuzzy_search_events,
                            fuzzy_search_games, fuzzy_search_matches, fuzzy_search_prize_distribution,
                            fuzzy_search_ewc_info, fuzzy_search_group_matches, fuzzy_search_transfers,
                            fuzzy_search_global_matches, fuzzy_search_ewc_teams_players,
                            fuzzy_search_player_information, fuzzy_search_team_information
                        )
                        
                        fuzzy_functions = {
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
                        
                        if search_type in fuzzy_functions:
                            table_results, table_total = fuzzy_functions[search_type](query, fuzzy_threshold, page, per_page)
                            results[search_type] = table_results
                            total = table_total
                    else:
                        results, total = fuzzy_global_search_extended(query, fuzzy_threshold, page, per_page)
                    
                    # Generate suggestions for misspelled queries
                    suggestions = suggest_corrections_extended(query)
                    
            except Exception as e:
                logger.error(f"Auto search error: {str(e)}")
                results, total = fuzzy_global_search_extended(query, fuzzy_threshold, page, per_page)
                suggestions = suggest_corrections_extended(query)
        
        elif search_mode == 'fts':
            # Full-text search only
            if search_type:
                from .fts_search import (
                    fts_search_news, fts_search_teams, fts_search_events,
                    fts_search_games, fts_search_matches, fts_search_prize_distribution,
                    fts_search_ewc_info, fts_search_group_matches, fts_search_transfers,
                    fts_search_global_matches, fts_search_ewc_teams_players,
                    fts_search_player_information, fts_search_team_information
                )
                
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
                
                if search_type in search_functions:
                    table_results, table_total = search_functions[search_type](query, page, per_page)
                    results[search_type] = table_results
                    total = table_total
            else:
                results, total = fts_global_search(query, page, per_page)
        
        elif search_mode == 'fuzzy':
            # Fuzzy search only
            if search_type:
                from .fuzzy_search_extended import (
                    fuzzy_search_news, fuzzy_search_teams, fuzzy_search_events,
                    fuzzy_search_games, fuzzy_search_matches, fuzzy_search_prize_distribution,
                    fuzzy_search_ewc_info, fuzzy_search_group_matches, fuzzy_search_transfers,
                    fuzzy_search_global_matches, fuzzy_search_ewc_teams_players,
                    fuzzy_search_player_information, fuzzy_search_team_information
                )
                
                fuzzy_functions = {
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
                
                if search_type in fuzzy_functions:
                    table_results, table_total = fuzzy_functions[search_type](query, fuzzy_threshold, page, per_page)
                    results[search_type] = table_results
                    total = table_total
            else:
                results, total = fuzzy_global_search_extended(query, fuzzy_threshold, page, per_page)
            
            suggestions = suggest_corrections_extended(query)
        
        elif search_mode == 'hybrid':
            # Combine FTS and fuzzy results
            fts_results, fts_total = fts_global_search(query, 1, per_page // 2)
            fuzzy_results, fuzzy_total = fuzzy_global_search_extended(query, fuzzy_threshold, 1, per_page // 2)
            
            # Merge results
            all_tables = set(fts_results.keys()) | set(fuzzy_results.keys())
            results = {}
            
            for table in all_tables:
                combined = []
                if table in fts_results:
                    combined.extend(fts_results[table])
                if table in fuzzy_results:
                    combined.extend(fuzzy_results[table])
                
                # Remove duplicates based on ID
                seen_ids = set()
                unique_results = []
                for item in combined:
                    item_id = item.get('id')
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        unique_results.append(item)
                
                results[table] = unique_results[:per_page]
            
            total = fts_total + fuzzy_total
            suggestions = suggest_corrections_extended(query)
        
        # Apply additional filters if provided
        if filters and results:
            results = apply_filters_extended(results, filters)
        
        execution_time = time.time() - start_time
        
        # Log the search query
        log_search_query(query, search_mode, total, execution_time)
        
        return {
            'results': results,
            'total': total,
            'search_mode': search_mode,
            'execution_time': execution_time,
            'suggestions': suggestions,
            'page': page,
            'per_page': per_page
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Enhanced search error: {str(e)}")
        
        # Log failed search
        log_search_query(query, search_mode, 0, execution_time, error=str(e))
        
        return {
            'results': {},
            'total': 0,
            'search_mode': search_mode,
            'execution_time': execution_time,
            'suggestions': suggest_corrections_extended(query),
            'error': str(e)
        }

def apply_filters_extended(results, filters):
    """Apply additional filters to search results"""
    if not filters:
        return results
    
    filtered_results = {}
    
    for table_name, table_results in results.items():
        filtered_table_results = []
        
        for result in table_results:
            include_result = True
            
            for filter_key, filter_value in filters.items():
                if filter_key in result:
                    result_value = str(result[filter_key]).lower()
                    filter_value = str(filter_value).lower()
                    
                    if filter_value not in result_value:
                        include_result = False
                        break
            
            if include_result:
                filtered_table_results.append(result)
        
        filtered_results[table_name] = filtered_table_results
    
    return filtered_results

def search_with_filters_extended(table_name, filters, page=1, per_page=10):
    """Search with specific field filters for any table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build WHERE clause from filters
        where_conditions = []
        params = []
        
        for field, value in filters.items():
            if value:
                where_conditions.append(f"{field} LIKE ?")
                params.append(f"%{value}%")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Count total results
        count_query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT ? OFFSET ?"
        cursor.execute(query, params + [per_page, offset])
        
        results = [dict(row) for row in cursor.fetchall()]
        
        return results, total
        
    except sqlite3.Error as e:
        logger.error(f"Filtered search error: {str(e)}")
        return [], 0
    finally:
        conn.close()

def get_all_table_names_extended():
    """Get list of all searchable table names"""
    return [
        'news', 'teams', 'events', 'games', 'matches', 'prize_distribution',
        'ewc_info', 'group_matches', 'transfers', 'global_matches',
        'ewc_teams_players', 'player_information', 'team_information'
    ]

def get_table_schema_extended(table_name):
    """Get schema information for a table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        schema = {}
        for column in columns:
            schema[column[1]] = {  # column[1] is the column name
                'type': column[2],  # column[2] is the data type
                'not_null': bool(column[3]),  # column[3] is not null flag
                'default': column[4],  # column[4] is default value
                'primary_key': bool(column[5])  # column[5] is primary key flag
            }
        
        return schema
        
    except sqlite3.Error as e:
        logger.error(f"Error getting table schema: {str(e)}")
        return {}
    finally:
        conn.close()

def get_searchable_fields_by_table():
    """Get searchable fields for each table"""
    return {
        'news': ['title', 'description', 'writer'],
        'teams': ['team_name'],
        'events': ['name'],
        'games': ['game_name', 'genre', 'platform', 'description'],
        'matches': ['game', 'group_name', 'team1_name', 'team2_name'],
        'prize_distribution': ['place', 'prize', 'participants'],
        'ewc_info': ['header', 'series', 'organizers', 'location', 'prize_pool', 'liquipedia_tier'],
        'group_matches': ['game', 'tournament', 'group_name', 'team1_name', 'team2_name'],
        'transfers': ['game', 'player_name', 'old_team_name', 'new_team_name'],
        'global_matches': ['game', 'tournament', 'group_name', 'team1_name', 'team2_name', 'status'],
        'ewc_teams_players': ['game', 'team_name', 'placement', 'tournament', 'players'],
        'player_information': ['game', 'player_page_name', 'data'],
        'team_information': ['game', 'team_page_name', 'data']
    }

