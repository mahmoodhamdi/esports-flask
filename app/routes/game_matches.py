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
                              team2_name:
                                type: string
                                example: "AimP"
                              stream_link:
                                type: string
                                example: "None"
      400:
        description: Bad request if 'live=true' and 'game' is not provided, or invalid day format.
      500:
        description: Internal server error for database or API issues.
    examples:
      application/json:
        tournaments:
          - tournament_name: "EPL Season 27"
            games:
              - game: "dota2"
                matches:
                  - id: 100
                    match_time: "July 1, 2025 - 14:30 CEST"
                    score: "2:::0"
                    status: "Completed"
                    team1_name: "eSpoiled"
                    team2_name: "AimP"
                    stream_link: "None"
                  - id: 95
                    match_time: "July 1, 2025 - 17:00 CEST"
                    score: "0:::2"
                    status: "Completed"
                    team1_name: "YeS"
                    team2_name: "Z10"
                    stream_link: "None"
    """
    game = request.args.get('game')
    status = request.args.get('status')
    tournament = request.args.get('tournament')
    day = request.args.get('day')
    live = request.args.get('live', 'false').lower() == 'true'

    try:
        if live:
            if not game:
                logger.warning("Game parameter missing for live=true")
                return jsonify({"error": "Game parameter is required when live=true"}), 400
            logger.info(f"Fetching fresh data for game={game}, day={day}")
            scrape_matches(game)
            results = get_game_matches(game, status, tournament, day)
        else:
            results = get_game_matches(game, status, tournament, day)
            logger.info(f"Found {len(results)} tournaments for live=false, game={game}, day={day}")

        return jsonify({"tournaments": results})

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return jsonify({"error": str(e)}), 400
    except (sqlite3.Error, requests.RequestException) as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": "Internal server error"}), 500