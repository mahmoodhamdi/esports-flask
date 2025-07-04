import sqlite3
import logging
import time
from flask import request
from .db import get_connection
from .fts_search import fts_global_search, fts_search_news, fts_search_teams, fts_search_events, fts_search_games, fts_search_matches
from .fuzzy_search import fuzzy_global_search, suggest_corrections
from .optimized_pagination import OptimizedOffsetPagination, CursorPagination
from .search_logger import log_search_query

logger = logging.getLogger(__name__)

class EnhancedSearch:
    """Enhanced search class that combines FTS, fuzzy search, and optimized pagination"""
    
    def __init__(self):
        self.fts_functions = {
            'news': fts_search_news,
            'teams': fts_search_teams,
            'events': fts_search_events,
            'games': fts_search_games,
            'matches': fts_search_matches
        }
    
    def search(self, query, search_type=None, page=1, per_page=10, search_mode='auto', 
               fuzzy_threshold=70, use_cursor=False, cursor=None):
        """
        Enhanced search with multiple search modes
        
        Args:
            query: Search query
            search_type: Specific table to search ('news', 'teams', etc.) or None for global
            page: Page number for offset pagination
            per_page: Items per page
            search_mode: 'fts', 'fuzzy', 'auto', or 'hybrid'
            fuzzy_threshold: Threshold for fuzzy matching (0-100)
            use_cursor: Whether to use cursor-based pagination
            cursor: Cursor for cursor-based pagination
        """
        start_time = time.time()
        
        try:
            if search_mode == 'auto':
                # Auto mode: try FTS first, fall back to fuzzy if no results
                results, total = self._auto_search(query, search_type, page, per_page, fuzzy_threshold)
            elif search_mode == 'fts':
                # Full-text search only
                results, total = self._fts_search(query, search_type, page, per_page)
            elif search_mode == 'fuzzy':
                # Fuzzy search only
                results, total = self._fuzzy_search(query, search_type, page, per_page, fuzzy_threshold)
            elif search_mode == 'hybrid':
                # Hybrid: combine FTS and fuzzy results
                results, total = self._hybrid_search(query, search_type, page, per_page, fuzzy_threshold)
            else:
                # Default to auto mode
                results, total = self._auto_search(query, search_type, page, per_page, fuzzy_threshold)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log the search
            self._log_search(query, search_type, execution_time, total, page, per_page)
            
            # Prepare response
            response = {
                'query': query,
                'search_mode': search_mode,
                'execution_time': round(execution_time, 3),
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page if total else 0
                }
            }
            
            # Add results
            if search_type:
                response[search_type] = results
            else:
                response.update(results)
            
            # Add suggestions for low result counts
            if total < 3 and query:
                suggestions = suggest_corrections(query)
                if suggestions:
                    response['suggestions'] = suggestions
            
            return response
            
        except Exception as e:
            logger.error(f"Enhanced search error: {str(e)}")
            return {
                'query': query,
                'error': str(e),
                'pagination': {'total': 0, 'page': page, 'per_page': per_page, 'total_pages': 0}
            }
    
    def _auto_search(self, query, search_type, page, per_page, fuzzy_threshold):
        """Auto search: FTS first, then fuzzy if needed"""
        # Try FTS first
        results, total = self._fts_search(query, search_type, page, per_page)
        
        # If FTS returns few results, try fuzzy search
        if total < 3:
            fuzzy_results, fuzzy_total = self._fuzzy_search(query, search_type, page, per_page, fuzzy_threshold)
            
            # Use fuzzy results if they're better
            if fuzzy_total > total:
                return fuzzy_results, fuzzy_total
        
        return results, total
    
    def _fts_search(self, query, search_type, page, per_page):
        """Full-text search using FTS5"""
        if search_type and search_type in self.fts_functions:
            return self.fts_functions[search_type](query, page, per_page)
        else:
            return fts_global_search(query, page, per_page)
    
    def _fuzzy_search(self, query, search_type, page, per_page, threshold):
        """Fuzzy search for handling misspellings"""
        if search_type:
            from .fuzzy_search import (fuzzy_search_news, fuzzy_search_teams, 
                                     fuzzy_search_events, fuzzy_search_games, fuzzy_search_matches)
            
            fuzzy_functions = {
                'news': fuzzy_search_news,
                'teams': fuzzy_search_teams,
                'events': fuzzy_search_events,
                'games': fuzzy_search_games,
                'matches': fuzzy_search_matches
            }
            
            if search_type in fuzzy_functions:
                return fuzzy_functions[search_type](query, threshold, page, per_page)
            else:
                return [], 0
        else:
            return fuzzy_global_search(query, threshold, page, per_page)
    
    def _hybrid_search(self, query, search_type, page, per_page, fuzzy_threshold):
        """Hybrid search: combine FTS and fuzzy results"""
        # Get FTS results
        fts_results, fts_total = self._fts_search(query, search_type, page, per_page)
        
        # Get fuzzy results
        fuzzy_results, fuzzy_total = self._fuzzy_search(query, search_type, page, per_page, fuzzy_threshold)
        
        # Combine and deduplicate results
        if search_type:
            # For single table search
            combined_results = self._merge_results(fts_results, fuzzy_results)
            return combined_results[:per_page], len(combined_results)
        else:
            # For global search
            combined_results = {}
            total_count = 0
            
            for table in ['news', 'teams', 'events', 'games', 'matches']:
                fts_table_results = fts_results.get(table, [])
                fuzzy_table_results = fuzzy_results.get(table, [])
                
                merged = self._merge_results(fts_table_results, fuzzy_table_results)
                combined_results[table] = merged
                total_count += len(merged)
            
            return combined_results, total_count
    
    def _merge_results(self, list1, list2):
        """Merge two result lists and remove duplicates based on ID"""
        seen_ids = set()
        merged = []
        
        # Add results from first list
        for item in list1:
            if item.get('id') not in seen_ids:
                merged.append(item)
                seen_ids.add(item.get('id'))
        
        # Add unique results from second list
        for item in list2:
            if item.get('id') not in seen_ids:
                merged.append(item)
                seen_ids.add(item.get('id'))
        
        return merged
    
    def _log_search(self, query, search_type, execution_time, result_count, page, per_page):
        """Log search query with performance metrics"""
        try:
            user_ip = request.remote_addr if request else None
            user_agent = request.headers.get('User-Agent', '') if request else ''
            
            log_search_query(
                query=query,
                search_type=search_type,
                execution_time=execution_time,
                result_count=result_count,
                page=page,
                per_page=per_page,
                user_ip=user_ip,
                user_agent=user_agent
            )
        except Exception as e:
            logger.error(f"Error logging search: {str(e)}")

def search_with_filters(table_name, filters, page=1, per_page=10, order_by='id', order_direction='ASC'):
    """
    Search with multiple filters and optimized pagination
    
    Args:
        table_name: Name of the table to search
        filters: Dictionary of field:value filters
        page: Page number
        per_page: Items per page
        order_by: Field to order by
        order_direction: ASC or DESC
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build WHERE clause from filters
        where_conditions = []
        params = []
        
        for field, value in filters.items():
            if value is not None:
                where_conditions.append(f"{field} LIKE ?")
                params.append(f"%{value}%")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else ""
        
        # Use optimized pagination
        paginator = OptimizedOffsetPagination()
        result = paginator.paginate_with_index_hint(
            table_name=table_name,
            where_clause=where_clause,
            order_by=order_by,
            order_direction=order_direction,
            page=page,
            per_page=per_page,
            params=params
        )
        
        return result
        
    except sqlite3.Error as e:
        logger.error(f"Filtered search error: {str(e)}")
        return {
            'data': [], 'page': page, 'per_page': per_page,
            'total': 0, 'total_pages': 0, 'has_next': False
        }

# Global enhanced search instance
enhanced_search = EnhancedSearch()

