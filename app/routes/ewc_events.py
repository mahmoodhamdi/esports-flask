# app/routes/ewc_events.py
from flask import Blueprint, request, jsonify
from app.ewc_events import get_ewc_events

events_bp = Blueprint('events', __name__)

@events_bp.route('/ewc_events', methods=['GET'])
def get_events():
    """
    Retrieve Esports World Cup 2025 events
    ---
    tags:
      - EWC Events
    summary: Get Esports World Cup events from Liquipedia or local cache
    description: >
      Returns a list of Esports World Cup 2025 event names and their links.
      If `live=true` is passed, data is fetched live from Liquipedia and stored in the local database.
      Otherwise, cached data is retrieved from the local SQLite database.
    parameters:
      - name: live
        in: query
        type: boolean
        required: false
        default: false
        description: If true, fetch live data from Liquipedia and update cache
    responses:
      200:
        description: A list of events retrieved successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Events data retrieved successfully
            data:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                    example: PUBG Mobile
                  link:
                    type: string
                    example: https://liquipedia.net/pubg/PUBG_Mobile_World_Invitational/2025
      500:
        description: Server error while fetching or parsing events data
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Server error: failed to fetch events from Liquipedia"
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
