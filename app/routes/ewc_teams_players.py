from flask import Blueprint, request, jsonify
from app.ewc_teams_players import fetch_ewc_teams_players
from flasgger import swag_from

teams_players_bp = Blueprint("teams_players", __name__)

@teams_players_bp.route("/ewc_teams_players", methods=["GET"])
@swag_from({
    "tags": [
        "Teams & Players"
    ],
    "parameters": [
        {
            "name": "game",
            "in": "query",
            "type": "string",
            "required": False,
            "default": "valorant",
            "description": "Game name (e.g., valorant, dota2, freefire)"
        },
        {
            "name": "page_title",
            "in": "query",
            "type": "string",
            "required": False,
            "default": "Esports_World_Cup/2025",
            "description": "Liquipedia page title"
        },
        {
            "name": "live",
            "in": "query",
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "If true, fetch data live from Liquipedia. If false, use cached data from the database."
        },
        {
            "name": "team_name",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by team name (partial match, case-insensitive)"
        },
        {
            "name": "player_name",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by player name (partial match, case-insensitive)"
        },
        {
            "name": "country",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by player country (partial match, case-insensitive)"
        },
        {
            "name": "has_won_before",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Filter by whether player has won before (true/false)"
        },
        {
            "name": "search",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "General search query across team name, player name, country, and tournament"
        }
    ],
    "responses": {
        200: {
            "description": "Successfully retrieved teams and players data",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Team": {
                                    "type": "string",
                                    "example": "Team Liquid"
                                },
                                "Placement": {
                                    "type": "string",
                                    "example": "1st"
                                },
                                "Tournament": {
                                    "type": "string",
                                    "example": "Esports World Cup 2025"
                                },
                                "Tournament_Logo": {
                                    "type": "string",
                                    "example": "https://liquipedia.net/commons/images/..."
                                },
                                "Years": {
                                    "type": "string",
                                    "example": "2025"
                                },
                                "Players": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "Role": {
                                                "type": "string",
                                                "example": "Duelist"
                                            },
                                            "Country": {
                                                "type": "string",
                                                "example": "United States"
                                            },
                                            "country_logo": {
                                                "type": "string",
                                                "example": "https://liquipedia.net/commons/images/..."
                                            },
                                            "Player": {
                                                "type": "string",
                                                "example": "TenZ"
                                            },
                                            "HasWonBefore": {
                                                "type": "boolean",
                                                "example": True
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "message": {
                        "type": "string",
                        "example": "Teams and players data retrieved successfully"
                    },
                    "source": {
                        "type": "string",
                        "example": "live",
                        "description": "Indicates whether data was fetched from 'live' API or 'cache'"
                    },
                    "total_teams": {
                        "type": "integer",
                        "example": 16
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "error": {
                        "type": "string",
                        "example": "Failed to fetch teams and players data"
                    }
                }
            }
        }
    }
})
def get_ewc_teams_players():
    """
    Retrieve teams and players participating in the Esports World Cup 2025
    """
    try:
        # Get query parameters
        game = request.args.get("game", "valorant")
        page_title = request.args.get("page_title", "Esports_World_Cup/2025")
        live = request.args.get("live", "false").lower() == "true"
        team_name_filter = request.args.get("team_name")
        player_name_filter = request.args.get("player_name")
        country_filter = request.args.get("country")
        has_won_before_filter = request.args.get("has_won_before")
        if has_won_before_filter is not None:
            has_won_before_filter = has_won_before_filter.lower() == "true"
        search_query = request.args.get("search")
        
        # Fetch teams and players data
        teams_data = fetch_ewc_teams_players(
            game=game, 
            page_title=page_title, 
            live=live, 
            team_name_filter=team_name_filter, 
            player_name_filter=player_name_filter, 
            country_filter=country_filter, 
            has_won_before_filter=has_won_before_filter, 
            search_query=search_query
        )
        
        # Determine data source
        source = "live" if live else "cache"
        
        return jsonify({
            "success": True,
            "data": teams_data,
            "message": f"Teams and players data retrieved successfully from {source}",
            "source": source,
            "total_teams": len(teams_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to fetch teams and players data: {str(e)}"
        }), 500


@teams_players_bp.route("/ewc_teams_players/<game>", methods=["GET"])
@swag_from({
    "tags": [
        "Teams & Players"
    ],
    "parameters": [
        {
            "name": "game",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "Game name (e.g., valorant, dota2, freefire)"
        },
        {
            "name": "live",
            "in": "query",
            "type": "boolean",
            "required": False,
            "default": False,
            "description": "If true, fetch data live from Liquipedia. If false, use cached data from the database."
        },
        {
            "name": "team_name",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by team name (partial match, case-insensitive)"
        },
        {
            "name": "player_name",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by player name (partial match, case-insensitive)"
        },
        {
            "name": "country",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by player country (partial match, case-insensitive)"
        },
        {
            "name": "has_won_before",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Filter by whether player has won before (true/false)"
        },
        {
            "name": "search",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "General search query across team name, player name, country, and tournament"
        }
    ],
    "responses": {
        200: {
            "description": "Successfully retrieved teams and players data for the specified game"
        },
        500: {
            "description": "Internal server error"
        }
    }
})
def get_ewc_teams_players_by_game(game):
    """
    Retrieve teams and players for a specific game
    """
    try:
        # Get query parameters
        live = request.args.get("live", "false").lower() == "true"
        page_title = request.args.get("page_title", "Esports_World_Cup/2025")
        team_name_filter = request.args.get("team_name")
        player_name_filter = request.args.get("player_name")
        country_filter = request.args.get("country")
        has_won_before_filter = request.args.get("has_won_before")
        if has_won_before_filter is not None:
            has_won_before_filter = has_won_before_filter.lower() == "true"
        search_query = request.args.get("search")
        
        # Fetch teams and players data for specific game
        teams_data = fetch_ewc_teams_players(
            game=game, 
            page_title=page_title, 
            live=live, 
            team_name_filter=team_name_filter, 
            player_name_filter=player_name_filter, 
            country_filter=country_filter, 
            has_won_before_filter=has_won_before_filter, 
            search_query=search_query
        )
        
        # Determine data source
        source = "live" if live else "cache"
        
        return jsonify({
            "success": True,
            "data": teams_data,
            "message": f"Teams and players data for {game} retrieved successfully from {source}",
            "source": source,
            "game": game,
            "total_teams": len(teams_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to fetch teams and players data for {game}: {str(e)}"
        }), 500


