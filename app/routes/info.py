from flask import Blueprint, request, jsonify
from app.ewc_info import get_ewc_information

info_bp = Blueprint("info", __name__)

@info_bp.route("/ewc_info", methods=["GET"])
def get_ewc_info():
    """
    Get Esports World Cup 2025 information
    ---
    parameters:
      - name: live
        in: query
        type: boolean
        required: false
        description: Fetch live data from Liquipedia if true, otherwise use database
    responses:
      200:
        description: Successfully retrieved
      500:
        description: Internal Server Error
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
