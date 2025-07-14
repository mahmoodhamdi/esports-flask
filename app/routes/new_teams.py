from flask import Blueprint, request, jsonify
from app.crud.new_teams_crud import update_teams_in_db, get_teams
from app.new_teams import fetch_teams_from_json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define the Blueprint for the new_teams endpoint
new_teams_bp = Blueprint('new_teams', __name__)

@new_teams_bp.route('/new_teams', methods=['GET'])
def get_new_teams():
    """
    Handle GET requests to the /new_teams endpoint.
    Returns a paginated list of teams in the format matching teams_ewc.json.
    Supports optional filtering by name and game, and live updates from JSON.
    """
    try:
        # Check if live update from JSON is requested
        live = request.args.get('live', 'false').lower() == 'true'
        if live:
            logger.info("Fetching and updating teams from JSON")
            teams_data = fetch_teams_from_json()
            if not teams_data:
                logger.warning("No teams data fetched from JSON")
                return jsonify({"error": "Failed to fetch teams data"}), 500
            # Log the structure of teams_data for debugging
            logger.debug(f"Fetched teams_data: {[{k: v for k, v in team.items() if k != 'games'} for team in teams_data]}")
            logger.debug(f"Games for first team: {teams_data[0]['games'] if teams_data else []}")
            if not update_teams_in_db(teams_data):
                logger.error("Failed to update teams in database")
                return jsonify({"error": "Failed to update database"}), 500
            logger.info("Successfully updated database with JSON data")
        
        # Get query parameters for filtering and pagination
        name_filter = request.args.get('name')
        game_filter = request.args.get('game')
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            if page < 1 or per_page < 1:
                raise ValueError("Invalid page or per_page")
        except ValueError as e:
            logger.warning(f"Invalid pagination parameters: {e}")
            page, per_page = 1, 10
        
        logger.info(f"Fetching teams with name_filter: {name_filter}, game_filter: {game_filter}, page: {page}, per_page: {per_page}")
        result = get_teams(name_filter, game_filter, page, per_page)
        
        # Transform teams to match the teams_ewc.json format
        transformed_teams = [
            {
                "team_name": team["name"],
                "logo_url": team["logo_url"],
                "games": [
                    {
                        "game_name": game["game_name"],
                        "game_logos": game["game_logos"]
                    }
                    for game in team["games"]
                ]
            }
            for team in result["teams"]
        ]
        
        # Update the result with transformed teams while preserving pagination metadata
        result["teams"] = transformed_teams
        logger.debug(f"Returning {len(transformed_teams)} teams with games: {[len(t['games']) for t in transformed_teams]}")
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_new_teams: {e}")
        return jsonify({"error": "Internal server error"}), 500