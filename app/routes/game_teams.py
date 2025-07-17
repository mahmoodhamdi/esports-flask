from flask import Blueprint, request, jsonify
from app.crud.game_teams_crud import parse_and_update_teams, get_teams

new_teams_bp = Blueprint('new_teams', __name__)

@new_teams_bp.route('/new_teams', methods=['GET'])
def new_teams():
    """Handle GET requests to /api/new_teams with multiple filters."""
    live = request.args.get('live', default=False, type=bool)
    if live:
        result = parse_and_update_teams()
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
    
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    name = request.args.get('name', default=None, type=str)
    game = request.args.get('game', default=None, type=str)
    logo_mode = request.args.get('logo_mode', default=None, type=str)
    all_filter = request.args.get('all', default=None, type=str)
    
    teams, total = get_teams(page, per_page, name, game, logo_mode, all_filter)
    
    return jsonify({
        'teams': teams,
        'total': total,
        'page': page,
        'per_page': per_page
    })