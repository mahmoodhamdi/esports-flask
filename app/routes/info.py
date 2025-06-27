from flask import Blueprint, request, jsonify
from app.ewc_info import get_ewc_information

info_bp = Blueprint("info", __name__)

@info_bp.route("/ewc_info", methods=["GET"])
def get_ewc_info():
    """
    Get Esports World Cup 2025 general information
    ---
    summary: Retrieve EWC 2025 Info (Games, Teams, and More)
    operationId: getEwcInfo
    tags:
      - Esports Info
    parameters:
      - name: live
        in: query
        type: boolean
        required: false
        description: If true, fetch from Liquipedia directly, otherwise use cached DB
        example: false
    responses:
      200:
        description: Successfully retrieved EWC info
        schema:
          type: object
          properties:
            message:
              type: string
              example: EWC information retrieved successfully
            data:
              type: object
              description: General EWC info like teams, games, etc.
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
    try:
        data = get_ewc_information(live=live)
        if not data:
            return jsonify({"message": "No information found", "data": {}}), 200

        return jsonify({
            "message": "EWC information retrieved successfully",
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
