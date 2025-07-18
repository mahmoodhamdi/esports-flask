from flask import Blueprint, request, jsonify
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

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 10

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
                page=page,
                per_page=per_page
            ))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
