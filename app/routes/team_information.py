from flask import Blueprint, request, jsonify
from urllib.parse import urlparse, unquote
from app.crud.team_information_crud import get_team_info as get_team_info_db, save_team_info
from app.team_information import get_team_info as get_team_info_api,parse_liquipedia_url, get_team_info_by_url as get_team_info_api_by_url

team_information_bp = Blueprint('team_information', __name__)

@team_information_bp.route('/team_information', methods=['GET'])
def team_information():
    """
    Endpoint to fetch team information with live/db toggle and filters.
    
    Parameters:
    - url: Full Liquipedia URL (e.g., https://liquipedia.net/dota2/Team_Liquid)
    - game: Game name (legacy support)
    - team: Team name (legacy support)
    - live: 'true' to fetch from API, 'false' to fetch from DB (default: 'false')
    - fields: Comma-separated fields to filter response (optional)
    
    Examples:
    - /team_information?url=https://liquipedia.net/callofduty/Team_Falcons/Warzone&live=true
    - /team_information?game=dota2&team=Team_Liquid&live=false
    """
    # Check for URL parameter (new method)
    url = request.args.get('url')
    
    # Legacy parameters (old method)
    game = request.args.get('game')
    team = request.args.get('team')
    
    live = request.args.get('live', 'false').lower() == 'true'
    fields = request.args.get('fields')  # Optional: comma-separated fields to filter response

    # Determine which method to use
    if url:
        # New method: using full URL
        parsed_url = parse_liquipedia_url(url)
        if not parsed_url:
            return jsonify({"error": "Invalid Liquipedia URL format"}), 400
        
        game, team = parsed_url
        
    elif game and team:
        # Legacy method: using separate game and team parameters
        pass
        
    else:
        return jsonify({
            "error": "Missing required parameters. Provide either 'url' or both 'game' and 'team' parameters",
            "examples": {
                "url_method": "/team_information?url=https://liquipedia.net/callofduty/Team_Falcons/Warzone&live=true",
                "legacy_method": "/team_information?game=dota2&team=Team_Liquid&live=false"
            }
        }), 400

    try:
        if live:
            # Fetch from API
            if url:
                # Use URL-based API function if available
                data, _ = get_team_info_api_by_url(url)
            else:
                # Use legacy API function
                data, _ = get_team_info_api(game, team)
                
            if not data:
                return jsonify({"error": "Failed to fetch data from API"}), 500
                
            # Save to database
            if not save_team_info(game, team, data):
                return jsonify({"error": "Failed to save data to database"}), 500
        else:
            # Fetch from database
            data = get_team_info_db(game, team)
            if not data:
                return jsonify({
                    "error": "Data not found in database. Use live=true to fetch from API.",
                    "suggestion": f"Try: {request.base_url}?{'url=' + url if url else f'game={game}&team={team}'}&live=true"
                }), 404

        # Apply filters if 'fields' parameter is provided
        if fields:
            try:
                field_list = [f.strip() for f in fields.split(',')]
                filtered_data = {k: data[k] for k in field_list if k in data}
                
                # Add metadata about filtering
                response_data = {
                    "data": filtered_data,
                    "meta": {
                        "filtered": True,
                        "requested_fields": field_list,
                        "available_fields": list(data.keys()),
                        "returned_fields": list(filtered_data.keys())
                    }
                }
                return jsonify(response_data)
                
            except Exception as e:
                return jsonify({"error": f"Invalid fields parameter: {e}"}), 400

        # Return full data with metadata
        response_data = {
            "data": data,
            "meta": {
                "game": game,
                "team": team,
                "source": "api" if live else "database",
                "total_fields": len(data),
                "url_used": url if url else None
            }
        }
        
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@team_information_bp.route('/team_information/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "team_information",
        "supported_methods": ["url", "game+team"],
        "example_urls": [
            "/team_information?url=https://liquipedia.net/dota2/Team_Liquid",
            "/team_information?game=callofduty&team=Team_Falcons/Warzone",
            "/team_information?url=https://liquipedia.net/csgo/FaZe_Clan&live=true&fields=Name,Team_Information"
        ]
    })

# Additional utility endpoint
@team_information_bp.route('/team_information/parse_url', methods=['GET'])
def parse_url():
    """
    Utility endpoint to test URL parsing.
    
    Parameters:
    - url: Liquipedia URL to parse
    
    Example:
    - /team_information/parse_url?url=https://liquipedia.net/callofduty/Team_Falcons/Warzone
    """
    url = request.args.get('url')
    
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400
    
    parsed_result = parse_liquipedia_url(url)
    
    if parsed_result:
        game, team = parsed_result
        return jsonify({
            "success": True,
            "original_url": url,
            "parsed": {
                "game": game,
                "team": team
            },
            "api_equivalent": f"/team_information?game={game}&team={team}"
        })
    else:
        return jsonify({
            "success": False,
            "original_url": url,
            "error": "Invalid Liquipedia URL format"
        }), 400