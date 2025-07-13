import sqlite3
from flask import Blueprint, request, jsonify
import requests
from app.crud.game_matches_crud import get_game_matches
from app.game_matches import scrape_matches
import logging

logger = logging.getLogger(__name__)

game_matches_bp = Blueprint('game_matches', __name__)

@game_matches_bp.route('/game_matches', methods=['GET'])
def game_matches():
    """
    Fetch game matches with optional filters, grouped by tournament and game.
    ---
    parameters:
      - name: game
        in: query
        type: string
        required: false
        description: Filter matches by game name (e.g., 'dota2'). Required when live=true.
      - name: status
        in: query
        type: string
        required: false
        description: Filter matches by status (e.g., 'Upcoming', 'Completed').
      - name: tournament
        in: query
        type: string
        required: false
        description: Filter matches by tournament name (e.g., 'EPL Season 27').
      - name: day
        in: query
        type: string
        required: false
        description: Filter matches by specific day (format: 'YYYY-MM-DD'). Matches are sorted by match_time.
      - name: live
        in: query
        type: boolean
        required: false
        default: false
        description: If true, fetch fresh data from API; if false, use database and return empty array if no matches.
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Page number for pagination (minimum 1).
      - name: per_page
        in: query
        type: integer
        required: false
        default: 10
        description: Number of tournaments per page (minimum 1, maximum 100).
    responses:
      200:
        description: Matches fetched successfully, grouped by tournament and game, or empty array if none found.
        schema:
          type: object
          properties:
            tournaments:
              type: array
              items:
                type: object
                properties:
                  tournament_name:
                    type: string
                    example: "EPL Season 27"
                  tournament_image:
                    type: string
                    example: "https://liquipedia.net/tournament_icon.png"
                  games:
                    type: array
                    items:
                      type: object
                      properties:
                        game:
                          type: string
                          example: "dota2"
                        matches:
                          type: array
                          items:
                            type: object
                            properties:
                              id:
                                type: integer
                                example: 100
                              match_time:
                                type: string
                                example: "July 1, 2025 - 14:30 CEST"
                              score:
                                type: string
                                example: "2:::0"
                              status:
                                type: string
                                example: "Completed"
                              team1_name:
                                type: string
                                example: "eSpoiled"
                              team1_image:
                                type: string
                                example: "https://liquipedia.net/team1_logo.png"
                              team2_name:
                                type: string
                                example: "AimP"
                              team2_image:
                                type: string
                                example: "https://liquipedia.net/team2_logo.png"
                              stream_link:
                                type: string
                                example: "None"
            total:
              type: integer
              description: Total number of tournaments
              example: 20
            page:
              type: integer
              description: Current page number
              example: 1
            per_page:
              type: integer
              description: Number of tournaments per page
              example: 10
      400:
        description: Bad request if 'live=true' and 'game' is not provided, invalid day format, or invalid pagination parameters.
      500:
        description: Internal server error for database or API issues.
    examples:
      application/json:
        tournaments:
          - tournament_name: "EPL Season 27"
            tournament_image: "https://liquipedia.net/tournament_icon.png"
            games:
              - game: "dota2"
                matches:
                  - id: 100
                    match_time: "July 1, 2025 - 14:30 CEST"
                    score: "2:::0"
                    status: "Completed"
                    team1_name: "eSpoiled"
                    team1_image: "https://liquipedia.net/team1_logo.png"
                    team2_name: "AimP"
                    team2_image: "https://liquipedia.net/team2_logo.png"
                    stream_link: "None"
        total: 1
        page: 1
        per_page: 10
    """
    game = request.args.get('game')
    status = request.args.get('status')
    tournament = request.args.getlist('tournament')
    day = request.args.get('day')
    live = request.args.get('live', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Validate pagination parameters
    if page < 1:
        logger.warning(f"Invalid page number: {page}")
        return jsonify({"error": "Page number must be at least 1"}), 400
    if per_page < 1 or per_page > 100:
        logger.warning(f"Invalid per_page value: {per_page}")
        return jsonify({"error": "Per_page must be between 1 and 100"}), 400

    try:
        if live:
            if not game:
                logger.warning("Game parameter missing for live=true")
                return jsonify({"error": "Game parameter is required when live=true"}), 400
            logger.info(f"Fetching fresh data for game={game}, day={day}")
            scrape_matches(game)
        results = get_game_matches(game, status, tournament, day, page, per_page)
        logger.info(f"Found {results['total']} tournaments for live={live}, game={game}, day={day}, page={page}, per_page={per_page}")

        return jsonify(results)

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return jsonify({"error": str(e)}), 400
    except (sqlite3.Error, requests.RequestException) as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": "Internal server error"}), 500