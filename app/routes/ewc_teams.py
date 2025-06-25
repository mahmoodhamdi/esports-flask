from flask import Blueprint, request, jsonify
from app.ewc_teams import fetch_ewc_teams

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/ewc_teams', methods=['GET'])
def get_ewc_teams():
    """
    Get Esports World Cup 2025 teams data
    ---
    parameters:
      - name: live
        in: query
        type: boolean
        required: false
        description: Fetch live data from Liquipedia if true, otherwise use cached data
    responses:
      200:
        description: Successfully retrieved teams data
      500:
        description: Server error while fetching teams data
    """
    live = request.args.get('live', 'false').lower() == 'true'

    try:
        teams_data = fetch_ewc_teams(live=live)
        if not teams_data:
            return jsonify({
                "message": "No teams data found",
                "data": []
            }), 200

        return jsonify({
            "message": "Teams data retrieved successfully",
            "data": teams_data
        })
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500
