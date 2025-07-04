from flask import Blueprint, request, jsonify
from app.crud.search_crud import search_table, global_search
from app.search_logger import search_performance_decorator, get_search_analytics
from app.enhanced_search import enhanced_search, search_with_filters
from app.optimized_pagination import create_pagination_indexes
from app.fts_search import populate_fts_tables, rebuild_fts_indexes

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET'])
def search():
    """Enhanced search endpoint with multiple search modes"""
    query = request.args.get('query', '')
    search_type = request.args.get('search_type')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 10)), 100)  # Limit max per_page
    search_mode = request.args.get('search_mode', 'auto')  # auto, fts, fuzzy, hybrid
    fuzzy_threshold = int(request.args.get('fuzzy_threshold', 70))
    use_cursor = request.args.get('use_cursor', 'false').lower() == 'true'
    cursor = request.args.get('cursor')
    
    # Use enhanced search
    result = enhanced_search.search(
        query=query,
        search_type=search_type,
        page=page,
        per_page=per_page,
        search_mode=search_mode,
        fuzzy_threshold=fuzzy_threshold,
        use_cursor=use_cursor,
        cursor=cursor
    )
    
    return jsonify(result)

@search_bp.route('/search/legacy', methods=['GET'])
@search_performance_decorator
def search_legacy():
    """Legacy search endpoint for backward compatibility"""
    search_type = request.args.get('search_type')
    query = request.args.get('query', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    filter_field = request.args.get('filter_field')
    filter_value = request.args.get('filter_value')
    
    if search_type:
        # Search specific type with pagination
        results, total = search_table(search_type, query, page, per_page, filter_field, filter_value)
        response_data = {search_type: results}
        total_pages = (total + per_page - 1) // per_page
    else:
        # Global search
        results_by_type, total = global_search(query, page, per_page, filter_field, filter_value)
        response_data = results_by_type
        total_pages = (total + per_page - 1) // per_page
    
    return jsonify({
        **response_data,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        }
    })

@search_bp.route('/search/filtered', methods=['GET'])
def search_filtered():
    """Search with multiple filters"""
    table_name = request.args.get('table', 'news')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 10)), 100)
    order_by = request.args.get('order_by', 'id')
    order_direction = request.args.get('order_direction', 'ASC').upper()
    
    # Extract filters from query parameters
    filters = {}
    for key, value in request.args.items():
        if key not in ['table', 'page', 'per_page', 'order_by', 'order_direction'] and value:
            filters[key] = value
    
    result = search_with_filters(
        table_name=table_name,
        filters=filters,
        page=page,
        per_page=per_page,
        order_by=order_by,
        order_direction=order_direction
    )
    
    return jsonify(result)

@search_bp.route('/search/analytics', methods=['GET'])
def search_analytics():
    """Get search analytics and insights"""
    days = int(request.args.get('days', 30))
    limit = int(request.args.get('limit', 100))
    
    analytics = get_search_analytics(days, limit)
    
    return jsonify({
        'analytics': analytics,
        'period_days': days
    })

@search_bp.route('/search/suggestions', methods=['GET'])
def search_suggestions():
    """Get search suggestions for a query"""
    query = request.args.get('query', '')
    threshold = int(request.args.get('threshold', 60))
    
    if not query:
        return jsonify({'suggestions': []})
    
    from app.fuzzy_search import suggest_corrections
    suggestions = suggest_corrections(query, threshold)
    
    return jsonify({'suggestions': suggestions})

@search_bp.route('/search/admin/rebuild-indexes', methods=['POST'])
def rebuild_search_indexes():
    """Admin endpoint to rebuild search indexes"""
    try:
        # Create pagination indexes
        create_pagination_indexes()
        
        # Rebuild FTS indexes
        rebuild_fts_indexes()
        
        # Populate FTS tables
        populate_fts_tables()
        
        return jsonify({
            'message': 'Search indexes rebuilt successfully',
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'message': f'Error rebuilding indexes: {str(e)}',
            'status': 'error'
        }), 500

@search_bp.route('/search/admin/populate-fts', methods=['POST'])
def populate_fts():
    """Admin endpoint to populate FTS tables"""
    try:
        populate_fts_tables()
        return jsonify({
            'message': 'FTS tables populated successfully',
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'message': f'Error populating FTS tables: {str(e)}',
            'status': 'error'
        }), 500