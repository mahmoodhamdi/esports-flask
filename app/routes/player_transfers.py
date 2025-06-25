from flask import Blueprint, request, jsonify
import logging
import json
from ..player_transfers import (
    fetch_and_store_transfers,
    get_transfers_from_db,
    get_available_transfer_games,
    get_available_teams,
    get_available_players,
    delete_transfers,
    import_transfers_from_json
)

logger = logging.getLogger(__name__)

# Create blueprint
player_transfers_bp = Blueprint('player_transfers', __name__)

@player_transfers_bp.route('/player-transfers/fetch', methods=['POST'])
def fetch_transfers():
    """
    Fetch and store player transfers for a specific game
    ---
    tags:
      - Player Transfers
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
          required:
            - game
    responses:
      200:
        description: Transfers fetched successfully
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
            transfer_count:
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
        
        if not game:
            return jsonify({'error': 'Game is required'}), 400
        
        result = fetch_and_store_transfers(game)
        
        if result['status'] == 'error':
            return jsonify(result), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in fetch_transfers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_transfers_bp.route('/player-transfers', methods=['GET'])
def get_transfers():
    """
    Get player transfers with optional filters and pagination
    ---
    tags:
      - Player Transfers
    parameters:
      - name: game
        in: query
        type: string
        description: Filter by game
      - name: player_name
        in: query
        type: string
        description: Filter by player name (partial match)
      - name: old_team
        in: query
        type: string
        description: Filter by old team name (partial match)
      - name: new_team
        in: query
        type: string
        description: Filter by new team name (partial match)
      - name: date_from
        in: query
        type: string
        description: Filter transfers from this date (YYYY-MM-DD)
      - name: date_to
        in: query
        type: string
        description: Filter transfers to this date (YYYY-MM-DD)
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number for pagination
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Number of transfers per page (max 100)
      - name: sort_by
        in: query
        type: string
        default: date
        description: Sort by field (date, player_name, old_team_name, new_team_name, created_at)
      - name: sort_order
        in: query
        type: string
        default: desc
        description: Sort order (asc, desc)
    responses:
      200:
        description: Transfers retrieved successfully
        schema:
          type: object
          properties:
            transfers:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  unique_id:
                    type: string
                  game:
                    type: string
                  date:
                    type: string
                  player:
                    type: object
                    properties:
                      name:
                        type: string
                      flag:
                        type: string
                  old_team:
                    type: object
                    properties:
                      name:
                        type: string
                      logo_light:
                        type: string
                      logo_dark:
                        type: string
                  new_team:
                    type: object
                    properties:
                      name:
                        type: string
                      logo_light:
                        type: string
                      logo_dark:
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
        player_name = request.args.get('player_name')
        old_team = request.args.get('old_team')
        new_team = request.args.get('new_team')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        
        # Sorting parameters
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Validate page number
        if page < 1:
            page = 1
        
        if per_page < 1:
            per_page = 20
        
        result = get_transfers_from_db(
            game=game,
            player_name=player_name,
            old_team=old_team,
            new_team=new_team,
            date_from=date_from,
            date_to=date_to,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in get_transfers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_transfers_bp.route('/player-transfers/games', methods=['GET'])
def get_games():
    """
    Get list of available games with transfers
    ---
    tags:
      - Player Transfers
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
        games = get_available_transfer_games()
        return jsonify({'games': games}), 200
        
    except Exception as e:
        logger.error(f"Error in get_games: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_transfers_bp.route('/player-transfers/teams', methods=['GET'])
def get_teams():
    """
    Get list of available teams, optionally filtered by game
    ---
    tags:
      - Player Transfers
    parameters:
      - name: game
        in: query
        type: string
        description: Filter teams by game
    responses:
      200:
        description: Teams retrieved successfully
        schema:
          type: object
          properties:
            teams:
              type: array
              items:
                type: string
      500:
        description: Internal server error
    """
    try:
        game = request.args.get('game')
        teams = get_available_teams(game)
        return jsonify({'teams': teams}), 200
        
    except Exception as e:
        logger.error(f"Error in get_teams: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_transfers_bp.route('/player-transfers/players', methods=['GET'])
def get_players():
    """
    Get list of available players, optionally filtered by game
    ---
    tags:
      - Player Transfers
    parameters:
      - name: game
        in: query
        type: string
        description: Filter players by game
    responses:
      200:
        description: Players retrieved successfully
        schema:
          type: object
          properties:
            players:
              type: array
              items:
                type: string
      500:
        description: Internal server error
    """
    try:
        game = request.args.get('game')
        players = get_available_players(game)
        return jsonify({'players': players}), 200
        
    except Exception as e:
        logger.error(f"Error in get_players: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_transfers_bp.route('/player-transfers/delete', methods=['DELETE'])
def delete_transfers_endpoint():
    """
    Delete transfers from database
    ---
    tags:
      - Player Transfers
    parameters:
      - name: game
        in: query
        type: string
        description: Delete transfers for specific game
    responses:
      200:
        description: Transfers deleted successfully
        schema:
          type: object
          properties:
            status:
              type: string
            deleted_count:
              type: integer
      500:
        description: Internal server error
    """
    try:
        game = request.args.get('game')
        result = delete_transfers(game)
        
        if result['status'] == 'error':
            return jsonify(result), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in delete_transfers_endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_transfers_bp.route('/player-transfers/import', methods=['POST'])
def import_transfers():
    """
    Import transfers from JSON data
    ---
    tags:
      - Player Transfers
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            game:
              type: string
              description: Game name
              example: 'dota2'
            transfers:
              type: array
              description: Array of transfer objects
              items:
                type: object
                properties:
                  Date:
                    type: string
                  Players:
                    type: array
                    items:
                      type: object
                      properties:
                        Name:
                          type: string
                        Flag:
                          type: string
                  OldTeam:
                    type: object
                    properties:
                      Name:
                        type: string
                      Logo_Light:
                        type: string
                      Logo_Dark:
                        type: string
                  NewTeam:
                    type: object
                    properties:
                      Name:
                        type: string
                      Logo_Light:
                        type: string
                      Logo_Dark:
                        type: string
          required:
            - game
            - transfers
    responses:
      200:
        description: Transfers imported successfully
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
            transfer_count:
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
        transfers = data.get('transfers')
        
        if not game or not transfers:
            return jsonify({'error': 'Game and transfers are required'}), 400
        
        if not isinstance(transfers, list):
            return jsonify({'error': 'Transfers must be an array'}), 400
        
        result = import_transfers_from_json(game, transfers)
        
        if result['status'] == 'error':
            return jsonify(result), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in import_transfers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_transfers_bp.route('/player-transfers/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about stored transfers
    ---
    tags:
      - Player Transfers
    responses:
      200:
        description: Statistics retrieved successfully
        schema:
          type: object
          properties:
            total_transfers:
              type: integer
            games_count:
              type: integer
            teams_count:
              type: integer
            players_count:
              type: integer
            games:
              type: array
              items:
                type: object
                properties:
                  game:
                    type: string
                  transfer_count:
                    type: integer
            recent_transfers:
              type: array
              items:
                type: object
                properties:
                  date:
                    type: string
                  transfer_count:
                    type: integer
      500:
        description: Internal server error
    """
    try:
        from ..db import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get total transfers
        cursor.execute("SELECT COUNT(*) FROM transfers")
        total_transfers = cursor.fetchone()[0]
        
        # Get counts
        cursor.execute("SELECT COUNT(DISTINCT game) FROM transfers")
        games_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT team_name) FROM (
                SELECT old_team_name as team_name FROM transfers WHERE old_team_name != 'None'
                UNION
                SELECT new_team_name as team_name FROM transfers WHERE new_team_name != 'None'
            )
        """)
        teams_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT player_name) FROM transfers")
        players_count = cursor.fetchone()[0]
        
        # Get transfers per game
        cursor.execute("""
            SELECT game, COUNT(*) as transfer_count 
            FROM transfers 
            GROUP BY game 
            ORDER BY transfer_count DESC
        """)
        games_stats = [{'game': row[0], 'transfer_count': row[1]} for row in cursor.fetchall()]
        
        # Get recent transfers by date
        cursor.execute("""
            SELECT date, COUNT(*) as transfer_count 
            FROM transfers 
            GROUP BY date 
            ORDER BY date DESC 
            LIMIT 10
        """)
        recent_transfers = [{'date': row[0], 'transfer_count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_transfers': total_transfers,
            'games_count': games_count,
            'teams_count': teams_count,
            'players_count': players_count,
            'games': games_stats,
            'recent_transfers': recent_transfers
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

