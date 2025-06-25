from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.crud import get_games_from_db, store_games_in_db
from app.liquipedia import fetch_ewc_games_from_web

games_bp = Blueprint('games', __name__)

@games_bp.route("/ewc_games", methods=["GET"])
@swag_from({
    'tags': ['Games'],
    'parameters': [
        {
            'name': 'live',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'description': 'If true, fetch from Liquipedia and update the database'
        }
    ],
    'responses': {
        200: {
            'description': 'Games data retrieved successfully',
            'examples': {
                'application/json': {
                    "message": "Games data retrieved successfully",
                    "data": [
                        {
                            "game_name": "Dota 2",
                            "logo_url": "https://liquipedia.net/images/..."
                        },
                        {
                            "game_name": "League of Legends",
                            "logo_url": "https://liquipedia.net/images/..."
                        }
                    ]
                }
            }
        }
    }
})
def get_ewc_games():
    """
    Get Esports World Cup 2025 games
    ---
    """
    live = request.args.get("live", "false").lower() == "true"
    data = []

    if not live:
        data = get_games_from_db()
        if not data:
            data = fetch_ewc_games_from_web()
            if data:
                store_games_in_db(data)
    else:
        data = fetch_ewc_games_from_web()
        if data:
            store_games_in_db(data)

    return jsonify({
        "message": "Games data retrieved successfully",
        "data": data
    })
