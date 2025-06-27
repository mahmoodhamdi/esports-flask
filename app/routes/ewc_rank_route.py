from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.ewc_rank import get_ewc_rank_data
from app.crud import get_ewc_rank_from_db, store_ewc_rank_in_db

ewc_rank_bp = Blueprint("ewc_rank", __name__)

@ewc_rank_bp.route("/ewc_rank", methods=["GET"])
@swag_from({
    "tags": ["EWC Rank"],
    "summary": "Get Esports World Cup 2025 Club Championship Standings",
    "description": "Retrieve the club championship standings for the Esports World Cup 2025, categorized by week. Data includes team rankings, trends, logos, and points.",
    "parameters": [
        {
            "name": "live",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "If true, fetch live data from Liquipedia; otherwise, use cached data.",
            "default": False
        }
    ],
    "responses": {
        200: {
            "description": "Club championship standings retrieved successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Club championship standings retrieved successfully."
                    },
                    "data": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "example": "fc56d8c91ea68a137f4410a9e78d4b2a"},
                                    "Ranking": {"type": "string", "example": "1."}, 
                                    "Trend": {"type": "string", "example": "New"},
                                    "Team": {"type": "string", "example": "Porsche Coanda Esports Racing Team"},
                                    "Logo_Light": {"type": "string", "example": "https://liquipedia.net/commons/images/thumb/5/5a/Porsche_Coanda_Esports_Racing_Team_lightmode.png"},
                                    "Logo_Dark": {"type": "string", "example": "https://liquipedia.net/commons/images/thumb/d/d7/Porsche_Coanda_Esports_Racing_Team_darkmode.png"},
                                    "Points": {"type": "string", "example": "150"},
                                    "Total Rank": {"type": "string", "example": "150"}
                                }
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Server error while fetching club championship standings.",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Server error: Failed to fetch data from Liquipedia."
                    }
                }
            }
        }
    }
})
def get_ewc_rank():
    """Get Esports World Cup 2025 Club Championship Standings"""
    live = request.args.get("live", "false").lower() == "true"

    try:
        if live:
            data = get_ewc_rank_data(live=True)
            if data:
                store_ewc_rank_in_db(data)
        else:
            data = get_ewc_rank_from_db()
            if not data:
                data = get_ewc_rank_data(live=True)
                if data:
                    store_ewc_rank_in_db(data)

        if not data:
            return jsonify({"message": "No club championship standings data found.", "data": {}}), 200

        return jsonify({"message": "Club championship standings retrieved successfully.", "data": data})
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


