from flask import Blueprint, request, jsonify
import logging
from ..search_logger import log_search_query
from ..enhanced_search_extended import enhanced_search_extended, search_with_filters_extended, get_all_table_names_extended, get_table_schema_extended, get_searchable_fields_by_table
from ..fuzzy_search_extended import suggest_corrections_extended, get_table_field_suggestions_extended
from ..fts_search import populate_fts_tables, rebuild_fts_indexes

search_extended_bp = Blueprint('search_extended', __name__)
logger = logging.getLogger(__name__)

@search_extended_bp.route('/search', methods=['GET'])
def search():
    """Enhanced search endpoint with support for all database tables"""
    try:
        # Get query parameters
        query = request.args.get('query', '').strip()
        search_mode = request.args.get('search_mode', 'auto')  # auto, fts, fuzzy, hybrid
        search_type = request.args.get('search_type')  # specific table or None for all
        fuzzy_threshold = int(request.args.get('fuzzy_threshold', 70))
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)  # Max 100 results per page
        
        # Get additional filters
        filters = {}
        for key, value in request.args.items():
            if key not in ['query', 'search_mode', 'search_type', 'fuzzy_threshold', 'page', 'per_page'] and value:
                filters[key] = value
        
        if not query:
            return jsonify({
                'error': 'Query parameter is required',
                'available_tables': get_all_table_names_extended(),
                'searchable_fields': get_searchable_fields_by_table()
            }), 400
        
        # Perform enhanced search
        results = enhanced_search_extended(
            query=query,
            search_mode=search_mode,
            search_type=search_type,
            fuzzy_threshold=fuzzy_threshold,
            page=page,
            per_page=per_page,
            filters=filters
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@search_extended_bp.route('/search/suggestions', methods=['GET'])
def search_suggestions():
    """Get spelling suggestions for a query"""
    try:
        query = request.args.get('query', '').strip()
        threshold = int(request.args.get('threshold', 60))
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        suggestions = suggest_corrections_extended(query, threshold)
        
        return jsonify({
            'query': query,
            'suggestions': suggestions,
            'threshold': threshold
        })
        
    except Exception as e:
        logger.error(f"Suggestions endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@search_extended_bp.route('/search/filtered', methods=['GET'])
def filtered_search():
    """Search with specific field filters"""
    try:
        table_name = request.args.get('table')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        if not table_name:
            return jsonify({
                'error': 'Table parameter is required',
                'available_tables': get_all_table_names_extended()
            }), 400
        
        if table_name not in get_all_table_names_extended():
            return jsonify({
                'error': f'Invalid table name: {table_name}',
                'available_tables': get_all_table_names_extended()
            }), 400
        
        # Get filters from query parameters
        filters = {}
        for key, value in request.args.items():
            if key not in ['table', 'page', 'per_page'] and value:
                filters[key] = value
        
        if not filters:
            return jsonify({'error': 'At least one filter parameter is required'}), 400
        
        results, total = search_with_filters_extended(table_name, filters, page, per_page)
        
        return jsonify({
            'results': results,
            'total': total,
            'table': table_name,
            'filters': filters,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        logger.error(f"Filtered search endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@search_extended_bp.route('/search/analytics', methods=['GET'])
def search_analytics():
    """Get search analytics and insights"""
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 10))
        
        # Simple analytics without search_crud module
        return jsonify({
            'analytics': {
                'total_searches': 0,
                'avg_execution_time': 0,
                'success_rate': 100
            },
            'popular_searches': [],
            'period_days': days,
            'note': 'Analytics module not available in this version'
        })
        
    except Exception as e:
        logger.error(f"Analytics endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@search_extended_bp.route('/search/tables', methods=['GET'])
def get_tables():
    """Get list of all searchable tables and their schemas"""
    try:
        include_schema = request.args.get('include_schema', 'false').lower() == 'true'
        
        tables = get_all_table_names_extended()
        result = {
            'tables': tables,
            'searchable_fields': get_searchable_fields_by_table()
        }
        
        if include_schema:
            schemas = {}
            for table in tables:
                schemas[table] = get_table_schema_extended(table)
            result['schemas'] = schemas
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Tables endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@search_extended_bp.route('/search/field-suggestions', methods=['GET'])
def field_suggestions():
    """Get suggestions for a specific table field"""
    try:
        table_name = request.args.get('table')
        field_name = request.args.get('field')
        query = request.args.get('query', '').strip()
        threshold = int(request.args.get('threshold', 60))
        
        if not all([table_name, field_name, query]):
            return jsonify({
                'error': 'Table, field, and query parameters are required',
                'available_tables': get_all_table_names_extended(),
                'searchable_fields': get_searchable_fields_by_table()
            }), 400
        
        if table_name not in get_all_table_names_extended():
            return jsonify({
                'error': f'Invalid table name: {table_name}',
                'available_tables': get_all_table_names_extended()
            }), 400
        
        suggestions = get_table_field_suggestions_extended(table_name, field_name, query, threshold)
        
        return jsonify({
            'table': table_name,
            'field': field_name,
            'query': query,
            'suggestions': suggestions,
            'threshold': threshold
        })
        
    except Exception as e:
        logger.error(f"Field suggestions endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Admin endpoints
@search_extended_bp.route('/search/admin/populate-fts', methods=['POST'])
def populate_fts():
    """Populate FTS tables with existing data"""
    try:
        populate_fts_tables()
        return jsonify({'message': 'FTS tables populated successfully'})
        
    except Exception as e:
        logger.error(f"FTS population error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@search_extended_bp.route('/search/admin/rebuild-fts', methods=['POST'])
def rebuild_fts():
    """Rebuild FTS indexes"""
    try:
        rebuild_fts_indexes()
        return jsonify({'message': 'FTS indexes rebuilt successfully'})
        
    except Exception as e:
        logger.error(f"FTS rebuild error: {str(e)}")
        return jsonify({'error': str(e)}), 500

