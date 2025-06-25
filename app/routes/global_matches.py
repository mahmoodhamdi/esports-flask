from flask import Blueprint, request, jsonify
import logging
from ..global_matches import (
    fetch_and_store_matches,
    get_matches_from_db,
    get_available_games,
    get_available_tournaments,
    get_available_groups,
    delete_matches
)

logger = logging.getLogger(__name__)

# Create blueprint
global_matches_bp = Blueprint('global_matches', __name__)

@global_matches_bp.route('/global-matches/fetch', methods=['POST'])
def fetch_matches():
    """
    Fetch and store matches for a specific game and tournament
    ---
    tags:
      - Global Matches
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            game:
              type: string
              description: Game name (e.g., 'dota2', 'valorant')
              example: 'dota2'
            tournament:
              type: string
              description: Tournament name
              example: 'Esports_World_Cup/2025'
          required:
            - game
            - tournament
    responses:
      200:
        description: Matches fetched successfully
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
            match_count:
              type: integer
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        game = data.get('game')
        tournament = data.get('tournament')
        
        if not game or not tournament:
            return jsonify({'error': 'Game and tournament are required'}), 400
        
        result = fetch_and_store_matches(game, tournament)
        
        if result['status'] == 'error':
            return jsonify(result), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in fetch_matches: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@global_matches_bp.route('/global-matches', methods=['GET'])
def get_matches():
    """
    Get matches with optional filters and pagination
    ---
    tags:
      - Global Matches
    parameters:
      - name: game
        in: query
        type: string
        description: Filter by game
      - name: tournament
        in: query
        type: string
        description: Filter by tournament
      - name: group_name
        in: query
        type: string
        description: Filter by group name
      - name: team
        in: query
        type: string
        description: Filter by team name (searches both team1 and team2)
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number for pagination
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Number of matches per page (max 100)
      - name: sort_by
        in: query
        type: string
        default: match_time
        description: Sort by field (match_time, game, tournament, group_name, created_at)
      - name: sort_order
        in: query
        type: string
        default: asc
        description: Sort order (asc, desc)
    responses:
      200:
        description: Matches retrieved successfully
        schema:
          type: object
          properties:
            matches:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  game:
                    type: string
                  tournament:
                    type: string
                  group_name:
                    type: string
                  team1:
                    type: object
                    properties:
                      name:
                        type: string
                      logo:
                        type: string
                  team2:
                    type: object
                    properties:
                      name:
                        type: string
                      logo:
                        type: string
                  match_time:
                    type: string
                  score:
                    type: string
                  status:
                    type: string
                  created_at:
                    type: string
                  updated_at:
                    type: string
            pagination:
              type: object
              properties:
                page:
                  type: integer
                per_page:
                  type: integer
                total_count:
                  type: integer
                total_pages:
                  type: integer
                has_next:
                  type: boolean
                has_prev:
                  type: boolean
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    try:
        # Get query parameters
        game = request.args.get('game')
        tournament = request.args.get('tournament')
        group_name = request.args.get('group_name')
        team = request.args.get('team')
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        
        # Sorting parameters
        sort_by = request.args.get('sort_by', 'match_time')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Validate page number
        if page < 1:
            page = 1
        
        if per_page < 1:
            per_page = 20
        
        result = get_matches_from_db(
            game=game,
            tournament=tournament,
            group_name=group_name,
            team=team,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in get_matches: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@global_matches_bp.route('/global-matches/games', methods=['GET'])
def get_games():
    """
    Get list of available games
    ---
    tags:
      - Global Matches
    responses:
      200:
        description: Games retrieved successfully
        schema:
          type: object
          properties:
            games:
              type: array
              items:
                type: string
      500:
        description: Internal server error
    """
    try:
        games = get_available_games()
        return jsonify({'games': games}), 200
        
    except Exception as e:
        logger.error(f"Error in get_games: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@global_matches_bp.route('/global-matches/tournaments', methods=['GET'])
def get_tournaments():
    """
    Get list of available tournaments, optionally filtered by game
    ---
    tags:
      - Global Matches
    parameters:
      - name: game
        in: query
        type: string
        description: Filter tournaments by game
    responses:
      200:
        description: Tournaments retrieved successfully
        schema:
          type: object
          properties:
            tournaments:
              type: array
              items:
                type: string
      500:
        description: Internal server error
    """
    try:
        game = request.args.get('game')
        tournaments = get_available_tournaments(game)
        return jsonify({'tournaments': tournaments}), 200
        
    except Exception as e:
        logger.error(f"Error in get_tournaments: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@global_matches_bp.route('/global-matches/groups', methods=['GET'])
def get_groups():
    """
    Get list of available groups, optionally filtered by game and tournament
    ---
    tags:
      - Global Matches
    parameters:
      - name: game
        in: query
        type: string
        description: Filter groups by game
      - name: tournament
        in: query
        type: string
        description: Filter groups by tournament
    responses:
      200:
        description: Groups retrieved successfully
        schema:
          type: object
          properties:
            groups:
              type: array
              items:
                type: string
      500:
        description: Internal server error
    """
    try:
        game = request.args.get('game')
        tournament = request.args.get('tournament')
        groups = get_available_groups(game, tournament)
        return jsonify({'groups': groups}), 200
        
    except Exception as e:
        logger.error(f"Error in get_groups: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@global_matches_bp.route('/global-matches/delete', methods=['DELETE'])
def delete_matches_endpoint():
    """
    Delete matches from database
    ---
    tags:
      - Global Matches
    parameters:
      - name: game
        in: query
        type: string
        description: Delete matches for specific game
      - name: tournament
        in: query
        type: string
        description: Delete matches for specific tournament (requires game)
    responses:
      200:
        description: Matches deleted successfully
        schema:
          type: object
          properties:
            status:
              type: string
            deleted_count:
              type: integer
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    try:
        game = request.args.get('game')
        tournament = request.args.get('tournament')
        
        # If tournament is specified, game must also be specified
        if tournament and not game:
            return jsonify({'error': 'Game must be specified when tournament is provided'}), 400
        
        result = delete_matches(game, tournament)
        
        if result['status'] == 'error':
            return jsonify(result), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in delete_matches_endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@global_matches_bp.route('/global-matches/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about stored matches
    ---
    tags:
      - Global Matches
    responses:
      200:
        description: Statistics retrieved successfully
        schema:
          type: object
          properties:
            total_matches:
              type: integer
            games_count:
              type: integer
            tournaments_count:
              type: integer
            groups_count:
              type: integer
            games:
              type: array
              items:
                type: object
                properties:
                  game:
                    type: string
                  match_count:
                    type: integer
      500:
        description: Internal server error
    """
    try:
        from ..db import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get total matches
        cursor.execute("SELECT COUNT(*) FROM global_matches")
        total_matches = cursor.fetchone()[0]
        
        # Get counts
        cursor.execute("SELECT COUNT(DISTINCT game) FROM global_matches")
        games_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT tournament) FROM global_matches")
        tournaments_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT group_name) FROM global_matches")
        groups_count = cursor.fetchone()[0]
        
        # Get matches per game
        cursor.execute("""
            SELECT game, COUNT(*) as match_count 
            FROM global_matches 
            GROUP BY game 
            ORDER BY match_count DESC
        """)
        games_stats = [{'game': row[0], 'match_count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_matches': total_matches,
            'games_count': games_count,
            'tournaments_count': tournaments_count,
            'groups_count': groups_count,
            'games': games_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

