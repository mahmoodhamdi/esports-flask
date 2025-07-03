from flask import Blueprint, request, jsonify
from app.crud.search_crud import search_table, global_search

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET'])
def search():
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