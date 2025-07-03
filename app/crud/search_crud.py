import json
import re
import sqlite3
import logging
from typing import List, Dict, Tuple, Optional, Any
from app.db import get_connection

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_RESULTS_PER_TABLE = 1000
MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 500
MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 10
MAX_PAGE_NUMBER = 10000

# Search configuration
SEARCH_TYPES = {
    "news": "news",
    "teams": "teams", 
    "events": "events",
    "games": "games",
    "matches": "matches",
    "players": "player_information",
}

SEARCH_FIELDS = {
    "news": ["title", "description", "writer"],
    "teams": ["team_name"],
    "events": ["name"],
    "games": ["game_name", "description", "genre", "platform"],
    "matches": ["team1_name", "team2_name", "game", "tournament", "group_name"],
    "players": ["Name", "Player_Information.Romanized Name"],
}

FILTER_FIELDS = {
    "news": ["writer"],
    "teams": ["team_name"],
    "events": ["name"],
    "games": ["genre", "platform"],
    "matches": ["game", "tournament", "group_name"],
    "players": ["Nationality"],
}

# SQL injection prevention patterns
DANGEROUS_PATTERNS = [
    r'(\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|UNION|SELECT)\b)',
    r'(--|\#|\/\*|\*\/)',
    r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
    r'(\'\s*(OR|AND)\s*\'\d+\'\s*=\s*\'\d+)',
    r'(\bSCRIPT\b|\bONLOAD\b|\bONERROR\b)',
]

def sanitize_input(value: str) -> str:
    """Sanitize input to prevent SQL injection and XSS attacks."""
    if not isinstance(value, str):
        return str(value)
    
    # Remove potential SQL injection patterns
    for pattern in DANGEROUS_PATTERNS:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    value = re.sub(r'\s+', ' ', value).strip()
    
    # Remove potentially dangerous characters
    value = re.sub(r'[<>"\']', '', value)
    
    return value

def validate_search_params(search_type: Optional[str], query: str, page: int, per_page: int) -> Tuple[bool, str]:
    """Validate search parameters and return validation result."""
    try:
        # Validate search type
        if search_type and search_type not in SEARCH_TYPES:
            return False, f"Invalid search type. Supported types: {', '.join(SEARCH_TYPES.keys())}"
        
        # Validate query
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        if len(query) < MIN_QUERY_LENGTH:
            return False, f"Query must be at least {MIN_QUERY_LENGTH} characters long"
        
        if len(query) > MAX_QUERY_LENGTH:
            return False, f"Query must be less than {MAX_QUERY_LENGTH} characters long"
        
        # Validate pagination
        if page < 1:
            return False, "Page number must be positive"
        
        if page > MAX_PAGE_NUMBER:
            return False, f"Page number cannot exceed {MAX_PAGE_NUMBER}"
        
        if per_page < 1:
            return False, "Per page value must be positive"
        
        if per_page > MAX_PER_PAGE:
            return False, f"Per page value cannot exceed {MAX_PER_PAGE}"
        
        return True, ""
    
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False, "Invalid parameters"

def build_search_query(search_type: str, query: str, filter_field: Optional[str] = None, 
                      filter_value: Optional[str] = None) -> Tuple[str, List[str]]:
    """Build optimized SQL query with proper indexing and parameters."""
    table_name = SEARCH_TYPES[search_type]
    search_fields = SEARCH_FIELDS.get(search_type, [])
    
    if not search_fields:
        return "", []
    
    # Build WHERE clause for search
    where_clauses = []
    params = []
    
    # Use FTS (Full Text Search) if available, otherwise use LIKE with optimization
    for field in search_fields:
        where_clauses.append(f"LOWER({field}) LIKE LOWER(?)")
        params.append(f"%{query}%")
    
    base_where = " OR ".join(where_clauses)
    
    # Add filter conditions
    if filter_field and filter_value and filter_field in FILTER_FIELDS.get(search_type, []):
        base_where = f"({base_where}) AND {filter_field} = ?"
        params.append(filter_value)
    
    # Build complete query
    sql = f"SELECT * FROM {table_name} WHERE {base_where}"
    
    return sql, params

def search_json_table(search_type: str, query: str, page: int, per_page: int, 
                     filter_field: Optional[str] = None, filter_value: Optional[str] = None,
                     for_global_search: bool = False) -> Tuple[List[Dict], int]:
    """Search in JSON-based tables (player_information, team_information)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        table_name = SEARCH_TYPES[search_type]
        cursor.execute(f"SELECT data FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            return [], 0
        
        # Parse JSON data
        items = []
        for row in rows:
            try:
                data = json.loads(row['data'])
                items.append(data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON data in {table_name}")
                continue
        
        # Apply search filter
        if query:
            query_lower = query.lower()
            filtered_items = []
            
            for item in items:
                if search_type == "players":
                    name_match = query_lower in item.get("Name", "").lower()
                    romanized_match = query_lower in item.get("Player_Information", {}).get("Romanized Name", "").lower()
                    
                    if name_match or romanized_match:
                        filtered_items.append(item)
                else:
                    # Generic search for other JSON tables
                    item_str = json.dumps(item).lower()
                    if query_lower in item_str:
                        filtered_items.append(item)
            
            items = filtered_items
        
        # Apply additional filters
        if filter_field and filter_value:
            if search_type == "players" and filter_field == "Nationality":
                items = [
                    item for item in items 
                    if item.get("Player_Information", {}).get("Nationality", {}).get("text") == filter_value
                ]
        
        total = len(items)
        
        # Apply pagination
        if not for_global_search:
            start = (page - 1) * per_page
            end = start + per_page
            paginated_items = items[start:end]
        else:
            paginated_items = items[:MAX_RESULTS_PER_TABLE]
        
        return paginated_items, total
        
    except Exception as e:
        logger.error(f"Error searching JSON table {search_type}: {str(e)}")
        return [], 0
    finally:
        conn.close()

def search_sql_table(search_type: str, query: str, page: int, per_page: int,
                    filter_field: Optional[str] = None, filter_value: Optional[str] = None,
                    for_global_search: bool = False) -> Tuple[List[Dict], int]:
    """Search in SQL tables with optimized queries."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        sql, params = build_search_query(search_type, query, filter_field, filter_value)
        
        if not sql:
            return [], 0
        
        # Get total count with optimized query
        count_sql = sql.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]
        
        # Add pagination and ordering
        if not for_global_search:
            offset = (page - 1) * per_page
            sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([per_page, offset])
        else:
            sql += " ORDER BY id DESC LIMIT ?"
            params.append(MAX_RESULTS_PER_TABLE)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows], total
        
    except sqlite3.Error as e:
        logger.error(f"Database error in search_sql_table: {str(e)}")
        return [], 0
    except Exception as e:
        logger.error(f"Error searching SQL table {search_type}: {str(e)}")
        return [], 0
    finally:
        conn.close()

def search_table(search_type: str, query: str, page: int, per_page: int,
                filter_field: Optional[str] = None, filter_value: Optional[str] = None,
                for_global_search: bool = False) -> Tuple[List[Dict], int]:
    """Main search function that routes to appropriate search method."""
    try:
        # Validate inputs
        is_valid, error_msg = validate_search_params(search_type, query, page, per_page)
        if not is_valid:
            logger.warning(f"Invalid search parameters: {error_msg}")
            return [], 0
        
        # Sanitize inputs
        query = sanitize_input(query)
        if filter_field:
            filter_field = sanitize_input(filter_field)
        if filter_value:
            filter_value = sanitize_input(filter_value)
        
        # Check if search type exists
        if search_type not in SEARCH_TYPES:
            logger.warning(f"Invalid search type: {search_type}")
            return [], 0
        
        table_name = SEARCH_TYPES[search_type]
        
        # Route to appropriate search method
        if table_name in ["player_information", "team_information"]:
            return search_json_table(search_type, query, page, per_page, filter_field, filter_value, for_global_search)
        else:
            return search_sql_table(search_type, query, page, per_page, filter_field, filter_value, for_global_search)
            
    except Exception as e:
        logger.error(f"Unexpected error in search_table: {str(e)}")
        return [], 0

def global_search(query: str, page: int, per_page: int, 
                 filter_field: Optional[str] = None, filter_value: Optional[str] = None) -> Tuple[Dict[str, List], int]:
    """Perform global search across all tables with optimized performance."""
    try:
        # Validate global search parameters
        is_valid, error_msg = validate_search_params(None, query, page, per_page)
        if not is_valid:
            logger.warning(f"Invalid global search parameters: {error_msg}")
            return {search_type: [] for search_type in SEARCH_TYPES}, 0
        
        # Sanitize inputs
        query = sanitize_input(query)
        if filter_field:
            filter_field = sanitize_input(filter_field)
        if filter_value:
            filter_value = sanitize_input(filter_value)
        
        results_by_type = {}
        total = 0
        
        # Search each table type
        for search_type in SEARCH_TYPES:
            try:
                results, table_total = search_table(
                    search_type, query, 1, MAX_RESULTS_PER_TABLE, 
                    filter_field, filter_value, for_global_search=True
                )
                results_by_type[search_type] = results
                total += table_total
            except Exception as e:
                logger.error(f"Error searching {search_type}: {str(e)}")
                results_by_type[search_type] = []
        
        # Apply global pagination
        all_results = []
        for search_type, items in results_by_type.items():
            for item in items:
                item['_search_type'] = search_type  # Add metadata for pagination
                all_results.append(item)
        
        # Sort results by relevance (you can implement custom scoring here)
        # For now, we'll sort by most recent (if timestamp available)
        try:
            all_results.sort(key=lambda x: x.get('updated_at', x.get('created_at', '')), reverse=True)
        except:
            pass  # Keep original order if sorting fails
        
        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = all_results[start:end]
        
        # Rebuild results by type
        paginated_results_by_type = {search_type: [] for search_type in SEARCH_TYPES}
        for item in paginated_results:
            search_type = item.pop('_search_type', None)
            if search_type:
                paginated_results_by_type[search_type].append(item)
        
        return paginated_results_by_type, total
        
    except Exception as e:
        logger.error(f"Unexpected error in global_search: {str(e)}")
        return {search_type: [] for search_type in SEARCH_TYPES}, 0

def get_search_suggestions(query: str, limit: int = 5) -> List[str]:
    """Get search suggestions based on partial query."""
    try:
        if not query or len(query) < 2:
            return []
        
        query = sanitize_input(query)
        suggestions = set()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get suggestions from different tables
        suggestion_queries = [
            ("news", "SELECT DISTINCT title FROM news WHERE LOWER(title) LIKE LOWER(?) LIMIT ?"),
            ("teams", "SELECT DISTINCT team_name FROM teams WHERE LOWER(team_name) LIKE LOWER(?) LIMIT ?"),
            ("games", "SELECT DISTINCT game_name FROM games WHERE LOWER(game_name) LIKE LOWER(?) LIMIT ?"),
            ("events", "SELECT DISTINCT name FROM events WHERE LOWER(name) LIKE LOWER(?) LIMIT ?"),
        ]
        
        for table_name, sql in suggestion_queries:
            try:
                cursor.execute(sql, (f"%{query}%", limit))
                rows = cursor.fetchall()
                for row in rows:
                    suggestions.add(row[0])
                    if len(suggestions) >= limit:
                        break
            except Exception as e:
                logger.error(f"Error getting suggestions from {table_name}: {str(e)}")
                continue
        
        conn.close()
        return list(suggestions)[:limit]
        
    except Exception as e:
        logger.error(f"Error in get_search_suggestions: {str(e)}")
        return []

def get_search_stats() -> Dict[str, Any]:
    """Get search statistics for monitoring and optimization."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        for search_type, table_name in SEARCH_TYPES.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                stats[search_type] = {
                    'total_records': count,
                    'table_name': table_name
                }
            except Exception as e:
                logger.error(f"Error getting stats for {search_type}: {str(e)}")
                stats[search_type] = {
                    'total_records': 0,
                    'table_name': table_name,
                    'error': str(e)
                }
        
        conn.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error in get_search_stats: {str(e)}")
        return {}