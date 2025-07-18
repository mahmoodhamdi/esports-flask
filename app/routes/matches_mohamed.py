from flask import Blueprint, request, jsonify
from datetime import datetime
from app.matches_mohamed import (
    scrape_matches,
    save_matches_to_db,
    get_matches_paginated
)

matches_bp = Blueprint('matches', __name__)

@matches_bp.route("/matches_mohamed", methods=["GET"])
def get_matches():
    live = request.args.get("live", "false").lower() == "true"
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    day = request.args.get("day")  # New parameter: expected format "YYYY-MM-DD"

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 10

    # Validate day parameter if provided
    if day:
        try:
            datetime.strptime(day, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid day format. Expected format: YYYY-MM-DD (e.g., 2025-07-24)"}), 400

    try:
        if live:
            # ✅ في حالة live = true: لعبة واحدة فقط ولا يوجد فلاتر تانية
            game = request.args.get("game", "dota2")
            if not game:
                return jsonify({"error": "Missing required parameter: game"}), 400
            
            scraped_matches = scrape_matches(game)
            save_matches_to_db(game, scraped_matches)

            # استخدم نفس دالة الـ pagination بس بلعبة واحدة فقط
            return jsonify(get_matches_paginated(
                games=[game],
                day=day,  # Add day filter even for live matches
                page=page,
                per_page=per_page
            ))

        else:
            # ✅ في حالة live = false: فلاتر متعددة
            games = request.args.getlist("game")
            tournaments = request.args.getlist("tournament")

            return jsonify(get_matches_paginated(
                games=games,
                tournaments=tournaments,
                live=False,
                day=day,  # Add day filter
                page=page,
                per_page=per_page
            ))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Helper function for converting timestamp to EEST
def convert_timestamp_to_eest(timestamp: int) -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    dt_utc = datetime.utcfromtimestamp(timestamp).replace(tzinfo=ZoneInfo("UTC"))
    dt_eest = dt_utc.astimezone(ZoneInfo("Europe/Athens"))
    return dt_eest.strftime("%B %d, %Y - %H:%M EEST")


def ensure_upload_folder():
    """Create uploads directory if it doesn't exist"""
    import os
    import logging
    
    UPLOAD_FOLDER = "uploads"  # Define this appropriately
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        logger.info(f"Created upload folder: {UPLOAD_FOLDER}")


def create_matches_table():
    """Create matches table if it doesn't exist"""
    from app.db import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create matches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,      -- unique match ID
            game TEXT,                                  -- game name (e.g., dota2, valorant)
            status TEXT,                                -- match status (Upcoming, Completed, etc.)
            tournament TEXT,                            -- tournament name
            tournament_link TEXT,                       -- URL to the tournament page
            tournament_icon TEXT,                       -- tournament icon image URL
            team1 TEXT,                                 -- name of team 1
            logo1_light TEXT,                           -- team 1 logo (light theme)
            logo1_dark TEXT,                            -- team 1 logo (dark theme)
            team2 TEXT,                                 -- name of team 2
            logo2_light TEXT,                           -- team 2 logo (light theme)
            logo2_dark TEXT,                            -- team 2 logo (dark theme)
            score TEXT,                                 -- match score (e.g., 2:0)
            match_time TEXT,                            -- localized match time (EEST)
            format TEXT,                                -- format (e.g., Bo3)
            stream_link TEXT,                           -- stream URL
            match_group TEXT                            -- group or bracket name
        )
    ''')
    
    conn.commit()
    conn.close()