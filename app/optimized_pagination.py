import sqlite3
import logging
import base64
import json
from .db import get_connection

logger = logging.getLogger(__name__)

class CursorPagination:
    """Cursor-based pagination for better performance on large datasets"""
    
    def __init__(self, table_name, order_by='id', order_direction='ASC'):
        self.table_name = table_name
        self.order_by = order_by
        self.order_direction = order_direction.upper()
    
    def encode_cursor(self, value):
        """Encode cursor value to base64"""
        if value is None:
            return None
        cursor_data = {'value': value, 'order_by': self.order_by}
        cursor_json = json.dumps(cursor_data)
        return base64.b64encode(cursor_json.encode()).decode()
    
    def decode_cursor(self, cursor):
        """Decode cursor from base64"""
        if not cursor:
            return None
        try:
            cursor_json = base64.b64decode(cursor.encode()).decode()
            return json.loads(cursor_json)
        except (ValueError, json.JSONDecodeError):
            return None
    
    def paginate(self, query_base, params=None, limit=10, cursor=None, where_clause=""):
        """
        Perform cursor-based pagination
        
        Args:
            query_base: Base SELECT query without ORDER BY and LIMIT
            params: Query parameters
            limit: Number of items per page
            cursor: Cursor for pagination
            where_clause: Additional WHERE conditions
        """
        try:
            conn = get_connection()
            cursor_obj = conn.cursor()
            
            if params is None:
                params = []
            
            # Decode cursor
            cursor_data = self.decode_cursor(cursor) if cursor else None
            
            # Build the query
            if cursor_data:
                cursor_value = cursor_data['value']
                if self.order_direction == 'ASC':
                    cursor_condition = f"{self.order_by} > ?"
                else:
                    cursor_condition = f"{self.order_by} < ?"
                
                if where_clause:
                    where_clause = f"{where_clause} AND {cursor_condition}"
                else:
                    where_clause = f"WHERE {cursor_condition}"
                
                params.append(cursor_value)
            elif where_clause and not where_clause.strip().upper().startswith('WHERE'):
                where_clause = f"WHERE {where_clause}"
            
            # Final query
            query = f"{query_base} {where_clause} ORDER BY {self.order_by} {self.order_direction} LIMIT ?"
            params.append(limit + 1)  # Get one extra to check if there's a next page
            
            cursor_obj.execute(query, params)
            results = [dict(row) for row in cursor_obj.fetchall()]
            
            # Check if there's a next page
            has_next = len(results) > limit
            if has_next:
                results = results[:limit]  # Remove the extra item
            
            # Generate next cursor
            next_cursor = None
            if has_next and results:
                last_item = results[-1]
                next_cursor = self.encode_cursor(last_item[self.order_by])
            
            return {
                'data': results,
                'has_next': has_next,
                'next_cursor': next_cursor,
                'limit': limit
            }
            
        except sqlite3.Error as e:
            logger.error(f"Cursor pagination error: {str(e)}")
            return {'data': [], 'has_next': False, 'next_cursor': None, 'limit': limit}
        finally:
            conn.close()

class OptimizedOffsetPagination:
    """Optimized offset-based pagination with performance improvements"""
    
    @staticmethod
    def paginate_with_count_optimization(query_base, count_query, params=None, page=1, per_page=10):
        """
        Optimized pagination that avoids expensive COUNT(*) when possible
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if params is None:
                params = []
            
            offset = (page - 1) * per_page
            
            # Get results with one extra to check if there's a next page
            query = f"{query_base} LIMIT ? OFFSET ?"
            query_params = params + [per_page + 1, offset]
            
            cursor.execute(query, query_params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # Check if there's a next page
            has_next = len(results) > per_page
            if has_next:
                results = results[:per_page]
            
            # Only get total count if specifically needed (e.g., for first page or when requested)
            total = None
            if page == 1 or offset < 1000:  # Only count for early pages
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
            
            return {
                'data': results,
                'page': page,
                'per_page': per_page,
                'has_next': has_next,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page if total else None
            }
            
        except sqlite3.Error as e:
            logger.error(f"Optimized pagination error: {str(e)}")
            return {
                'data': [], 'page': page, 'per_page': per_page,
                'has_next': False, 'total': 0, 'total_pages': 0
            }
        finally:
            conn.close()
    
    @staticmethod
    def paginate_with_index_hint(table_name, where_clause="", order_by="id", 
                                order_direction="ASC", page=1, per_page=10, params=None):
        """
        Pagination with index hints for better performance
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if params is None:
                params = []
            
            offset = (page - 1) * per_page
            
            # Use index hint for better performance
            if where_clause:
                where_clause = f"WHERE {where_clause}"
            
            # Query with explicit index usage
            query = f"""
                SELECT * FROM {table_name} 
                {where_clause}
                ORDER BY {order_by} {order_direction}
                LIMIT ? OFFSET ?
            """
            
            query_params = params + [per_page, offset]
            cursor.execute(query, query_params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # Get count efficiently for small offsets
            if offset < 1000:
                count_query = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                total_pages = (total + per_page - 1) // per_page
            else:
                total = None
                total_pages = None
            
            return {
                'data': results,
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': len(results) == per_page
            }
            
        except sqlite3.Error as e:
            logger.error(f"Index-optimized pagination error: {str(e)}")
            return {
                'data': [], 'page': page, 'per_page': per_page,
                'total': 0, 'total_pages': 0, 'has_next': False
            }
        finally:
            conn.close()

def create_pagination_indexes():
    """Create indexes to optimize pagination queries"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create indexes for common pagination scenarios
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_news_updated_at ON news(updated_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_teams_team_name ON teams(team_name)",
            "CREATE INDEX IF NOT EXISTS idx_events_name ON events(name)",
            "CREATE INDEX IF NOT EXISTS idx_games_game_name ON games(game_name)",
            "CREATE INDEX IF NOT EXISTS idx_matches_match_date ON matches(match_date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_matches_game ON matches(game)",
            "CREATE INDEX IF NOT EXISTS idx_transfers_date ON transfers(date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_transfers_game ON transfers(game)",
            "CREATE INDEX IF NOT EXISTS idx_search_logs_created_at ON search_logs(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_search_logs_query ON search_logs(query)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        logger.info("Pagination indexes created successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Error creating pagination indexes: {str(e)}")
        raise
    finally:
        conn.close()

def get_optimized_search_results(table_name, search_field, query, page=1, per_page=10, 
                                order_by='id', order_direction='ASC'):
    """
    Get search results with optimized pagination
    """
    try:
        conn = get_connection()
        cursor_obj = conn.cursor()
        
        # Use parameterized query to prevent SQL injection
        where_clause = f"{search_field} LIKE ?"
        search_param = f"%{query}%"
        
        # Use optimized pagination
        paginator = OptimizedOffsetPagination()
        result = paginator.paginate_with_index_hint(
            table_name=table_name,
            where_clause=where_clause,
            order_by=order_by,
            order_direction=order_direction,
            page=page,
            per_page=per_page,
            params=[search_param]
        )
        
        return result
        
    except sqlite3.Error as e:
        logger.error(f"Optimized search error: {str(e)}")
        return {
            'data': [], 'page': page, 'per_page': per_page,
            'total': 0, 'total_pages': 0, 'has_next': False
        }

def get_cursor_based_results(table_name, cursor=None, limit=10, order_by='id', order_direction='ASC'):
    """
    Get results using cursor-based pagination
    """
    paginator = CursorPagination(table_name, order_by, order_direction)
    query_base = f"SELECT * FROM {table_name}"
    
    return paginator.paginate(query_base, limit=limit, cursor=cursor)

