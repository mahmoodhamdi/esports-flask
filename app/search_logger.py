import time
import sqlite3
import logging
from functools import wraps
from flask import request
from .db import get_connection

logger = logging.getLogger(__name__)

def log_search_query(query, search_type, execution_time, result_count, page=1, per_page=10, 
                    filter_field=None, filter_value=None, user_ip=None, user_agent=None):
    """Log search query with performance metrics"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_logs 
            (query, search_type, execution_time, result_count, page, per_page, 
             filter_field, filter_value, user_ip, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (query, search_type, execution_time, result_count, page, per_page,
              filter_field, filter_value, user_ip, user_agent))
        
        conn.commit()
        logger.debug(f"Logged search query: '{query}' with {result_count} results in {execution_time:.3f}s")
        
    except sqlite3.Error as e:
        logger.error(f"Failed to log search query: {str(e)}")
    finally:
        conn.close()

def search_performance_decorator(func):
    """Decorator to automatically log search performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Extract request parameters
        query = request.args.get('query', '')
        search_type = request.args.get('search_type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        filter_field = request.args.get('filter_field')
        filter_value = request.args.get('filter_value')
        user_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Execute the search function
        result = func(*args, **kwargs)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Extract result count from response
        result_count = 0
        if hasattr(result, 'json') and result.json:
            response_data = result.json
            if 'pagination' in response_data:
                result_count = response_data['pagination'].get('total', 0)
            else:
                # Count results from different categories
                for key in ['news', 'events', 'teams', 'matches', 'games']:
                    if key in response_data:
                        result_count += len(response_data[key])
        
        # Log the search query
        log_search_query(
            query=query,
            search_type=search_type,
            execution_time=execution_time,
            result_count=result_count,
            page=page,
            per_page=per_page,
            filter_field=filter_field,
            filter_value=filter_value,
            user_ip=user_ip,
            user_agent=user_agent
        )
        
        return result
    
    return wrapper

def get_search_analytics(days=30, limit=100):
    """Get search analytics for the specified number of days"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Popular searches
        cursor.execute('''
            SELECT query, COUNT(*) as search_count, AVG(execution_time) as avg_time,
                   AVG(result_count) as avg_results
            FROM search_logs 
            WHERE created_at >= datetime('now', '-{} days')
            AND query != ''
            GROUP BY query 
            ORDER BY search_count DESC 
            LIMIT ?
        '''.format(days), (limit,))
        
        popular_searches = [dict(row) for row in cursor.fetchall()]
        
        # Slow queries
        cursor.execute('''
            SELECT query, search_type, execution_time, result_count, created_at
            FROM search_logs 
            WHERE created_at >= datetime('now', '-{} days')
            ORDER BY execution_time DESC 
            LIMIT ?
        '''.format(days), (limit,))
        
        slow_queries = [dict(row) for row in cursor.fetchall()]
        
        # Search trends by day
        cursor.execute('''
            SELECT DATE(created_at) as search_date, COUNT(*) as search_count,
                   AVG(execution_time) as avg_time
            FROM search_logs 
            WHERE created_at >= datetime('now', '-{} days')
            GROUP BY DATE(created_at)
            ORDER BY search_date DESC
        '''.format(days))
        
        daily_trends = [dict(row) for row in cursor.fetchall()]
        
        return {
            'popular_searches': popular_searches,
            'slow_queries': slow_queries,
            'daily_trends': daily_trends
        }
        
    except sqlite3.Error as e:
        logger.error(f"Failed to get search analytics: {str(e)}")
        return {}
    finally:
        conn.close()

