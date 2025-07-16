from flask import Blueprint, request, jsonify
from app.ewc_info import get_ewc_information

info_bp = Blueprint("info", __name__)

@info_bp.route("/ewc_info", methods=["GET"])
def get_ewc_info():
    """
    Get tournament general information from Liquipedia
    ---
    summary: Retrieve tournament info (Games, Teams, and More)
    operationId: getTournamentInfo
    tags:
      - Esports Info
    parameters:
      - name: live
        in: query
        type: boolean
        required: false
        description: If true, fetch from Liquipedia directly, otherwise use cached DB
        example: false
      - name: url
        in: query
        type: string
        required: false
        description: Liquipedia URL of the tournament page
        example: https://liquipedia.net/esports/Esports_World_Cup/2025
    responses:
      200:
        description: Successfully retrieved info
        schema:
          type: object
          properties:
            message:
              type: string
              example: Tournament information retrieved successfully
            data:
              type: object
              description: General tournament info
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unexpected error occurred
    """
    live = request.args.get("live", "false").lower() == "true"
    url = request.args.get("url", "https://liquipedia.net/esports/Esports_World_Cup/2025")

    try:
        data = get_ewc_information(live=live, url=url)
        if not data:
            return jsonify({"message": "No information found", "data": {}}), 200

        return jsonify({
            "message": "Tournament information retrieved successfully",
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
