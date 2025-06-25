from flask import Blueprint, jsonify, request
from app.ewc_transfers import store_transfers_in_db, get_transfers_from_db

transfers_bp = Blueprint('transfers', __name__)

@transfers_bp.route('/ewc_transfers/update', methods=['POST'])
def update_transfers():
    """
    Scrape and store player transfers for a given game
    ---
    parameters:
      - name: game
        in: query
        type: string
        required: true
        description: Game name for transfers (e.g., 'valorant')
    responses:
      200:
        description: Transfers stored successfully
      400:
        description: Missing game parameter
      500:
        description: Server error while storing transfers
    """
    game_name = request.args.get('game', '').strip().lower()
    if not game_name:
        return jsonify({"error": "Missing required query parameter: game"}), 400

    success, message = store_transfers_in_db(game_name)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500


@transfers_bp.route('/ewc_transfers', methods=['GET'])
def list_transfers():
    """
    Retrieve stored player transfers optionally filtered by game with pagination and sorting
    ---
    parameters:
      - name: game
        in: query
        type: string
        required: false
        description: Game name to filter transfers (e.g., 'valorant')
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Page number for pagination
      - name: per_page
        in: query
        type: integer
        required: false
        default: 50
        description: Number of items per page
      - name: sort_by
        in: query
        type: string
        required: false
        default: date
        enum: ['date', 'player_name', 'game', 'old_team_name', 'new_team_name']
        description: Field to sort by
      - name: sort_order
        in: query
        type: string
        required: false
        default: desc
        enum: ['asc', 'desc']
        description: Sort direction
    responses:
      200:
        description: Transfers retrieved successfully
    """
    game_name = request.args.get('game', '').strip().lower() or None
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    sort_by = request.args.get('sort_by', 'date').lower()
    sort_order = request.args.get('sort_order', 'desc').lower()

    result = get_transfers_from_db(game_name, page, per_page, sort_by, sort_order)
    return jsonify({
        "message": "Transfers retrieved successfully",
        "total": result["total"],
        "page": result["page"],
        "per_page": result["per_page"],
        "data": result["data"]
    })
