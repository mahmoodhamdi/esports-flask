from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.ewc_rank import get_ewc_rank_data, get_available_weeks
from app.crud import get_ewc_rank_from_db, store_ewc_rank_in_db

ewc_rank_bp = Blueprint("ewc_rank", __name__)

@ewc_rank_bp.route("/ewc_rank", methods=["GET"])
@swag_from({
    "tags": ["EWC Rank"],
    "summary": "Get Esports World Cup 2025 Club Championship Standings with Pagination and Filters",
    "description": "Retrieve the club championship standings for the Esports World Cup 2025 with support for pagination, week filtering, and team name filtering. Data includes team rankings, trends, logos, and points.",
    "parameters": [
        {
            "name": "live",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "If true, fetch live data from Liquipedia; otherwise, use cached data.",
            "default": False
        },
        {
            "name": "week",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by specific week (e.g., 'Week 1', 'Week 2', etc.). Case-insensitive.",
            "enum": ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7"]
        },
        {
            "name": "team",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by team name (partial match, case-insensitive). Example: 'Porsche' will match 'Porsche Coanda Esports Racing Team'."
        },
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "required": False,
            "description": "Page number for pagination (1-based).",
            "default": 1,
            "minimum": 1
        },
        {
            "name": "per_page",
            "in": "query",
            "type": "integer",
            "required": False,
            "description": "Number of items per page.",
            "default": 10,
            "minimum": 1,
            "maximum": 100
        }
    ],
    "responses": {
        200: {
            "description": "Club championship standings retrieved successfully with pagination.",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Club championship standings retrieved successfully."
                    },
                    "data": {
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
                                "Total Rank": {"type": "string", "example": "150"},
                                "Week": {"type": "string", "example": "Week 1"}
                            }
                        }
                    },
                    "pagination": {
                        "type": "object",
                        "properties": {
                            "current_page": {"type": "integer", "example": 1},
                            "per_page": {"type": "integer", "example": 10},
                            "total_items": {"type": "integer", "example": 45},
                            "total_pages": {"type": "integer", "example": 5},
                            "has_next": {"type": "boolean", "example": True},
                            "has_prev": {"type": "boolean", "example": False},
                            "next_page": {"type": "integer", "example": 2},
                            "prev_page": {"type": "integer", "example": None}
                        }
                    },
                    "filters": {
                        "type": "object",
                        "properties": {
                            "week": {"type": "string", "example": "Week 1"},
                            "team": {"type": "string", "example": "Porsche"}
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request - Invalid parameters.",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Invalid page number. Must be a positive integer."
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
    """Get Esports World Cup 2025 Club Championship Standings with Pagination and Filters"""
    try:
        # Parse query parameters
        live = request.args.get("live", "false").lower() == "true"
        week = request.args.get("week", None)
        team = request.args.get("team", None)
        
        # Parse pagination parameters with validation
        try:
            page = int(request.args.get("page", 1))
            if page < 1:
                return jsonify({"error": "Invalid page number. Must be a positive integer."}), 400
        except ValueError:
            return jsonify({"error": "Invalid page number. Must be a positive integer."}), 400
        
        try:
            per_page = int(request.args.get("per_page", 10))
            if per_page < 1 or per_page > 100:
                return jsonify({"error": "Invalid per_page value. Must be between 1 and 100."}), 400
        except ValueError:
            return jsonify({"error": "Invalid per_page value. Must be a positive integer."}), 400
        
        # Validate week parameter
        if week:
            available_weeks = get_available_weeks()
            if week not in available_weeks:
                return jsonify({
                    "error": f"Invalid week. Available weeks: {', '.join(available_weeks)}"
                }), 400
        
        # Get data with filters and pagination
        result = get_ewc_rank_data(
            live=live,
            week=week,
            team=team,
            page=page,
            per_page=per_page
        )
        
        if not result or not result.get("data"):
            return jsonify({
                "message": "No club championship standings data found.",
                "data": [],
                "pagination": {
                    "current_page": page,
                    "per_page": per_page,
                    "total_items": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False,
                    "next_page": None,
                    "prev_page": None
                },
                "filters": {
                    "week": week,
                    "team": team
                }
            }), 200
        
        return jsonify({
            "message": "Club championship standings retrieved successfully.",
            **result
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@ewc_rank_bp.route("/ewc_rank/weeks", methods=["GET"])
@swag_from({
    "tags": ["EWC Rank"],
    "summary": "Get Available Weeks",
    "description": "Retrieve the list of available weeks for filtering EWC rank data.",
    "responses": {
        200: {
            "description": "Available weeks retrieved successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Available weeks retrieved successfully."
                    },
                    "weeks": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "example": ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7"]
                    }
                }
            }
        }
    }
})
def get_weeks():
    """Get Available Weeks for Filtering"""
    try:
        weeks = get_available_weeks()
        return jsonify({
            "message": "Available weeks retrieved successfully.",
            "weeks": weeks
        })
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


