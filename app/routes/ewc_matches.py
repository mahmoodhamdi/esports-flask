from flask import Blueprint, jsonify, request
from app.ewc_matches import store_matches_in_db, get_all_matches_from_db
from datetime import datetime as dt

matches_bp = Blueprint('matches', __name__)

@matches_bp.route('/ewc_matches/update', methods=['POST'])
def update_matches():
    """
    Scrape and store all EWC matches into DB
    ---
    responses:
      200:
        description: Matches stored successfully
      500:
        description: Server error while storing matches
    """
    success, message = store_matches_in_db()
    if success:
        return jsonify({"message": message}), 200
    return jsonify({"error": message}), 500


@matches_bp.route('/ewc_matches', methods=['GET'])


@matches_bp.route('/api/ewc_matches', methods=['GET'])
def list_matches():
    """
    List all stored EWC matches with optional filters, sorting and pagination
    ---
    parameters:
      - name: game
        in: query
        type: string
        required: false
        description: Filter by game name (exact match, case insensitive)
      - name: group
        in: query
        type: string
        required: false
        description: Filter by group name (exact match, case insensitive)
      - name: date
        in: query
        type: string
        required: false
        description: Filter by match_date (format YYYY-MM-DD)
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Page number (starting from 1)
      - name: per_page
        in: query
        type: integer
        required: false
        default: 20
        description: Number of items per page (max 100)
    responses:
      200:
        description: Successfully retrieved filtered matches
    """
    try:
        game_filter = request.args.get('game', '').strip().lower()
        group_filter = request.args.get('group', '').strip().lower()
        date_filter = request.args.get('date', '').strip()
        page = max(1, request.args.get('page', 1, type=int))
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(max(1, per_page), 100)

        all_matches = get_all_matches_from_db()

        # فلترة
        filtered = []
        for m in all_matches:
            if game_filter and m['game'].lower() != game_filter:
                continue
            if group_filter and m['group_name'].lower() != group_filter:
                continue
            if date_filter and m['match_date'] != date_filter:
                continue
            filtered.append(m)

        # ترتيب حسب match_date ثم match_time
        def parse_dt(m):
            try:
                date = dt.strptime(m['match_date'], '%Y-%m-%d')
            except:
                date = dt.max
            try:
                time = dt.strptime(m['match_time'], '%H:%M').time()
            except:
                time = dt.max.time()
            return (date, time)

        filtered.sort(key=parse_dt)

        # تصفح صفحات
        total = len(filtered)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = filtered[start:end]

        return jsonify({
            "message": "Matches retrieved successfully",
            "page": page,
            "per_page": per_page,
            "total_matches": total,
            "matches": paginated
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
