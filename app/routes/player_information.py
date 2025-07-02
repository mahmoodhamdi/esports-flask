from flask import Blueprint, request, jsonify
from app.crud.player_information_crud import get_player_info as get_player_info_db, save_player_info
from app.player_information import get_player_info as get_player_info_api

player_information_bp = Blueprint('player_information', __name__)

@player_information_bp.route('/player_information', methods=['GET'])
def player_information():
    """Endpoint to fetch player information with live/db toggle and filters."""
    game = request.args.get('game')
    player = request.args.get('player')
    live = request.args.get('live', 'false').lower() == 'true'
    fields = request.args.get('fields')  # Optional: comma-separated fields to filter response

    if not game or not player:
        return jsonify({"error": "Missing 'game' or 'player' parameter"}), 400

    if live:
        data, _ = get_player_info_api(game, player)
        if not data:
            return jsonify({"error": "Failed to fetch data from API"}), 500
        if not save_player_info(game, player, data):
            return jsonify({"error": "Failed to save data to database"}), 500
    else:
        data = get_player_info_db(game, player)
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