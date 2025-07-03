from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import logging
from typing import Dict, Any
from app.crud.search_crud import (
    search_table, 
    global_search, 
    get_search_suggestions,
    get_search_stats,
    SEARCH_TYPES,
    MAX_PER_PAGE,
    DEFAULT_PER_PAGE
)

# Configure logging
logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)

# Supported search types for API documentation
SUPPORTED_SEARCH_TYPES = list(SEARCH_TYPES.keys())

def create_error_response(message: str, status_code: int = 400, error_code: str = None) -> tuple:
    """Create standardized error response."""
    response = {
        'error': True,
        'message': message,
        'data': None
    }
    if error_code:
        response['error_code'] = error_code
    
    return jsonify(response), status_code

def create_success_response(data: Dict[str, Any], message: str = "Success") -> tuple:
    """Create standardized success response."""
    response = {
        'error': False,
        'message': message,
        'data': data
    }
    return jsonify(response), 200

def validate_and_sanitize_params(request_args) -> tuple:
    """Validate and sanitize request parameters."""
    try:
        # Extract parameters
        search_type = request_args.get('search_type', '').strip()
        query = request_args.get('query', '').strip()
        page = request_args.get('page', 1)
        per_page = request_args.get('per_page', DEFAULT_PER_PAGE)
        filter_field = request_args.get('filter_field', '').strip()
        filter_value = request_args.get('filter_value', '').strip()
        
        # Validate and convert page
        try:
            page = int(page)
            if page < 1:
                return None, "Page number must be positive"
        except (ValueError, TypeError):
            return None, "Page must be a valid integer"
        
        # Validate and convert per_page
        try:
            per_page = int(per_page)
            if per_page < 1:
                return None, "Per page value must be positive"
            if per_page > MAX_PER_PAGE:
                return None, f"Per page value cannot exceed {MAX_PER_PAGE}"
        except (ValueError, TypeError):
            return None, "Per page must be a valid integer"
        
        # Validate search_type if provided
        if search_type and search_type not in SUPPORTED_SEARCH_TYPES:
            return None, f"Invalid search type. Supported types: {', '.join(SUPPORTED_SEARCH_TYPES)}"
        
        # Convert empty strings to None
        search_type = search_type if search_type else None
        filter_field = filter_field if filter_field else None
        filter_value = filter_value if filter_value else None
        
        params = {
            'search_type': search_type,
            'query': query,
            'page': page,
            'per_page': per_page,
            'filter_field': filter_field,
            'filter_value': filter_value
        }
        
        return params, None
        
    except Exception as e:
        logger.error(f"Parameter validation error: {str(e)}")
        return None, "Invalid request parameters"

@search_bp.route('/search', methods=['GET'])
def search():
    """
    Main search endpoint with comprehensive error handling.
    
    Query Parameters:
    - search_type: Optional specific search type (news, teams, events, games, matches, players)
    - query: Search query string (required)
    - page: Page number (default: 1)
    - per_page: Results per page (default: 10, max: 100)
    - filter_field: Optional filter field
    - filter_value: Optional filter value
    """
    try:
        # Validate and sanitize parameters
        params, error_msg = validate_and_sanitize_params(request.args)
        if error_msg:
            return create_error_response(error_msg, 400, "INVALID_PARAMS")
        
        search_type = params['search_type']
        query = params['query']
        page = params['page']
        per_page = params['per_page']
        filter_field = params['filter_field']
        filter_value = params['filter_value']
        
        # Validate query
        if not query:
            return create_error_response("Query parameter is required", 400, "MISSING_QUERY")
        
        if len(query) < 2:
            return create_error_response("Query must be at least 2 characters long", 400, "QUERY_TOO_SHORT")
        
        if len(query) > 500:
            return create_error_response("Query must be less than 500 characters long", 400, "QUERY_TOO_LONG")
        
        # Perform search
        if search_type:
            # Specific search type
            try:
                results, total = search_table(search_type, query, page, per_page, filter_field, filter_value)
                response_data = {search_type: results}
            except Exception as e:
                logger.error(f"Search error for type {search_type}: {str(e)}")
                return create_error_response("Search failed", 500, "SEARCH_ERROR")
        else:
            # Global search
            try:
                results_by_type, total = global_search(query, page, per_page, filter_field, filter_value)
                response_data = results_by_type
            except Exception as e:
                logger.error(f"Global search error: {str(e)}")
                return create_error_response("Global search failed", 500, "GLOBAL_SEARCH_ERROR")
        
        # Calculate pagination info
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        # Prepare response
        data = {
            **response_data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1,
                'next_page': page + 1 if page < total_pages else None,
                'prev_page': page - 1 if page > 1 else None
            },
            'search_info': {
                'query': query,
                'search_type': search_type,
                'filter_field': filter_field,
                'filter_value': filter_value
            }
        }
        
        return create_success_response(data, f"Found {total} results")
        
    except BadRequest as e:
        logger.warning(f"Bad request in search: {str(e)}")
        return create_error_response("Invalid request", 400, "BAD_REQUEST")
    except Exception as e:
        logger.error(f"Unexpected error in search endpoint: {str(e)}")
        return create_error_response("Internal server error", 500, "INTERNAL_ERROR")

@search_bp.route('/search/suggestions', methods=['GET'])
def search_suggestions():
    """
    Get search suggestions based on partial query.
    
    Query Parameters:
    - query: Partial search query (required)
    - limit: Number of suggestions to return (default: 5, max: 20)
    """
    try:
        query = request.args.get('query', '').strip()
        limit = request.args.get('limit', 5)
        
        # Validate query
        if not query:
            return create_error_response("Query parameter is required", 400, "MISSING_QUERY")
        
        if len(query) < 2:
            return create_error_response("Query must be at least 2 characters long", 400, "QUERY_TOO_SHORT")
        
        # Validate limit
        try:
            limit = int(limit)
            if limit < 1:
                limit = 5
            elif limit > 20:
                limit = 20
        except (ValueError, TypeError):
            limit = 5
        
        # Get suggestions
        suggestions = get_search_suggestions(query, limit)
        
        data = {
            'suggestions': suggestions,
            'query': query,
            'limit': limit
        }
        
        return create_success_response(data, f"Found {len(suggestions)} suggestions")
        
    except Exception as e:
        logger.error(f"Error in search suggestions endpoint: {str(e)}")
        return create_error_response("Failed to get suggestions", 500, "SUGGESTIONS_ERROR")

@search_bp.route('/search/stats', methods=['GET'])
def search_statistics():
    """
    Get search statistics and database info.
    """
    try:
        stats = get_search_stats()
        
        data = {
            'stats': stats,
            'supported_types': SUPPORTED_SEARCH_TYPES,
            'config': {
                'max_per_page': MAX_PER_PAGE,
                'default_per_page': DEFAULT_PER_PAGE
            }
        }
        
        return create_success_response(data, "Statistics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error in search statistics endpoint: {str(e)}")
        return create_error_response("Failed to get statistics", 500, "STATS_ERROR")

@search_bp.route('/search/health', methods=['GET'])
def search_health():
    """
    Health check endpoint for the search service.
    """
    try:
        # Simple health check
        stats = get_search_stats()
        
        data = {
            'status': 'healthy',
            'timestamp': 'current_timestamp',
            'total_tables': len(SEARCH_TYPES),
            'available_types': SUPPORTED_SEARCH_TYPES
        }
        
        return create_success_response(data, "Search service is healthy")
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_error_response("Search service is unhealthy", 500, "HEALTH_CHECK_FAILED")

@search_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors for search routes."""
    return create_error_response("Endpoint not found", 404, "NOT_FOUND")

@search_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors for search routes."""
    return create_error_response("Method not allowed", 405, "METHOD_NOT_ALLOWED")

@search_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors for search routes."""
    logger.error(f"Internal server error: {str(error)}")
    return create_error_response("Internal server error", 500, "INTERNAL_ERROR")