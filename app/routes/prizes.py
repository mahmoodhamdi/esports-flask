from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.prizes import get_prize_distribution
import logging

logger = logging.getLogger(__name__)

prize_bp = Blueprint('prize', __name__)
@prize_bp.route("/ewc_prize_distribution", methods=["GET"])
@swag_from({
    'tags': ['Prize'],
    'parameters': [
        {
            'name': 'live',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'description': 'Fetch from Liquipedia if true, else use DB'
        },
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'default': 1,
            'description': 'Page number'
        },
        {
            'name': 'per_page',
            'in': 'query',
            'type': 'integer',
            'default': 10,
            'description': 'Number of items per page'
        },
        {
            'name': 'filter',
            'in': 'query',
            'type': 'string',
            'description': 'Filter by place or prize'
        },
        {
            'name': 'url',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Custom Liquipedia page URL to fetch prize distribution'
        }
    ],
    'responses': {
        200: {
            'description': 'Prize distribution retrieved',
            'examples': {
                'application/json': {
                    "message": "Prize distribution data retrieved successfully",
                    "data": [],
                    "pagination": {}
                }
            }
        }
    }
})
def get_ewc_prize_distribution():
    live = request.args.get('live', 'false').lower() == 'true'
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    filter_query = request.args.get('filter', '').strip()
    url = request.args.get('url', None)

    try:
        prize_data = get_prize_distribution(live=live, url=url)
        if not prize_data:
            return jsonify({
                "message": "No prize distribution data found",
                "data": [],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": 0,
                    "pages": 0
                }
            }), 200

        if filter_query:
            filtered_data = [
                item for item in prize_data
                if filter_query.lower() in item['place'].lower() or
                   filter_query.lower() in item['prize'].lower()
            ]
        else:
            filtered_data = prize_data

        total = len(filtered_data)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = filtered_data[start:end]

        return jsonify({
            "message": "Prize distribution data retrieved successfully",
            "data": paginated,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
