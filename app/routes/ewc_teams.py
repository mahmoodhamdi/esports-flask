from flask import Blueprint, request, jsonify
from app.ewc_teams import fetch_ewc_teams

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/ewc_teams', methods=['GET'])
def get_ewc_teams():
    """
    Retrieve teams participating in the Esports World Cup 2025
    ---
    tags:
      - Teams
    parameters:
      - name: live
        in: query
        type: boolean
        required: false
        default: false
        description: If true, fetch data live from Liquipedia. If false, use cached data from the database.
    responses:
      200:
        description: Successfully retrieved teams data
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Teams data retrieved successfully"
            data:
              type: array
              items:
                type: object
                properties:
                  team_name:
                    type: string
                    example: "Team Falcons"
                  logo_url:
                    type: string
                    example: "https://liquipedia.net/images/..."
      500:
        description: Server error while fetching teams data
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Server error: Connection failed"
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
