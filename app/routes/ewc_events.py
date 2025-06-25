# app/routes/ewc_events.py
from flask import Blueprint, request, jsonify
from app.ewc_events import get_ewc_events

events_bp = Blueprint('events', __name__)

@events_bp.route('/ewc_events', methods=['GET'])
def get_events():
    """
    Get Esports World Cup 2025 events data
    ---
    parameters:
      - name: live
        in: query
        type: boolean
        required: false
        description: Fetch live data from Liquipedia if true
    responses:
      200:
        description: Successfully retrieved events data
      500:
        description: Server error while fetching events data
    """
    live = request.args.get('live', 'false').lower() == 'true'

    try:
        events_data = get_ewc_events(live=live)
        if not events_data:
            return jsonify({
                "message": "No events data found",
                "data": []
            }), 200

        return jsonify({
            "message": "Events data retrieved successfully",
            "data": events_data
        })
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500
