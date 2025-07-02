from flask import Blueprint, request, jsonify
from app.crud.team_information_crud import get_team_info as get_team_info_db, save_team_info
from app.team_information import get_team_info as get_team_info_api

team_information_bp = Blueprint('team_information', __name__)

@team_information_bp.route('/team_information', methods=['GET'])
def team_information():
    """Endpoint to fetch team information with live/db toggle and filters."""
    game = request.args.get('game')
    team = request.args.get('team')
    live = request.args.get('live', 'false').lower() == 'true'
    fields = request.args.get('fields')  # Optional: comma-separated fields to filter response

    if not game or not team:
        return jsonify({"error": "Missing 'game' or 'team' parameter"}), 400

    if live:
        data, _ = get_team_info_api(game, team)
        if not data:
            return jsonify({"error": "Failed to fetch data from API"}), 500
        if not save_team_info(game, team, data):
            return jsonify({"error": "Failed to save data to database"}), 500
    else:
        data = get_team_info_db(game, team)
        if not data:
            return jsonify({"error": "Data not found in database. Use live=true to fetch."}), 404

    # Apply filters if 'fields' parameter is provided
    if fields:
        try:
            field_list = [f.strip() for f in fields.split(',')]
            filtered_data = {k: data[k] for k in field_list if k in data}
            return jsonify(filtered_data)
        except Exception as e:
            return jsonify({"error": f"Invalid fields parameter: {e}"}), 400

    return jsonify(data)