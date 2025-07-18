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


