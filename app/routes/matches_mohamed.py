from flask import Blueprint, request, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from app.matches_mohamed import (
    scrape_matches,
    save_matches_to_db,
    get_matches_paginated
)

matches_bp = Blueprint('matches', __name__)

# قائمة المناطق الزمنية المدعومة
SUPPORTED_TIMEZONES = [
    'Africa/Cairo', 'Europe/London', 'Europe/Berlin', 'Europe/Athens',
    'America/New_York', 'America/Los_Angeles', 'America/Chicago', 'America/Denver',
    'Asia/Tokyo', 'Asia/Seoul', 'Asia/Singapore', 'Asia/Kolkata',
    'Australia/Sydney', 'UTC'
]

@matches_bp.route("/matches_mohamed", methods=["GET"])
def get_matches():
    """
    API endpoint لجلب المباريات مع دعم المناطق الزمنية
    
    Parameters:
    - live (bool): true للمباريات المباشرة، false للكل
    - game (str): اسم اللعبة (مطلوب عند live=true)
    - games (list): قائمة الألعاب للفلترة (عند live=false)
    - tournaments (list): قائمة البطولات للفلترة
    - day (str): تاريخ بصيغة YYYY-MM-DD
    - timezone (str): المنطقة الزمنية للمستخدم (IANA format)
    - page (int): رقم الصفحة (default: 1)
    - per_page (int): عدد العناصر في الصفحة (default: 10, max: 100)
    
    Returns:
    JSON response with tournaments and matches data
    """
    try:
        # استخراج المعاملات
        live = request.args.get("live", "false").lower() == "true"
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        day = request.args.get("day")
        timezone = request.args.get("timezone", "UTC")

        # التحقق من صحة المعاملات
        if page < 1:
            return jsonify({"error": "Page number must be greater than 0"}), 400
        if per_page < 1 or per_page > 100:
            return jsonify({"error": "per_page must be between 1 and 100"}), 400

        # التحقق من صحة التاريخ
        if day:
            try:
                datetime.strptime(day, "%Y-%m-%d")
            except ValueError:
                return jsonify({
                    "error": "Invalid day format. Expected format: YYYY-MM-DD (e.g., 2025-07-24)",
                    "example": "2025-07-24"
                }), 400

        # التحقق من صحة المنطقة الزمنية
        try:
            ZoneInfo(timezone)
        except Exception:
            return jsonify({
                "error": f"Invalid timezone: {timezone}",
                "message": "Please use IANA timezone format",
                "examples": SUPPORTED_TIMEZONES
            }), 400

        # معالجة الطلبات المباشرة (live=true)
        if live:
            game = request.args.get("game")
            if not game:
                return jsonify({
                    "error": "Missing required parameter: game",
                    "message": "When live=true, you must specify a game"
                }), 400

            print(f"🔄 Scraping live matches for {game}...")
            scraped_matches = scrape_matches(game,use_matches_page=True)
            save_matches_to_db(game, scraped_matches)
            print(f"✅ Saved {game} matches to database")

            result = get_matches_paginated(
                games=[game],
                day=day,
                page=page,
                per_page=per_page,
                timezone=timezone
            )

            result["metadata"] = {
                "live_data": True,
                "game": game,
                "timezone": timezone,
                "scraped_at": datetime.now(ZoneInfo('UTC')).isoformat(),
                "day_filter": day if day else None
            }
            return jsonify(result)

        # معالجة الطلبات العادية (live=false)
        else:
            games = request.args.getlist("game")
            tournaments = request.args.getlist("tournament")

            print(f"📊 Fetching matches from database...")
            if games:
                print(f"   Games filter: {games}")
            if tournaments:
                print(f"   Tournaments filter: {tournaments}")
            if day:
                print(f"   Day filter: {day}")
            if timezone:
                print(f"   Timezone: {timezone}")

            result = get_matches_paginated(
                games=games,
                tournaments=tournaments,
                live=False,
                day=day,
                page=page,
                per_page=per_page,
                timezone=timezone
            )

            # إضافة metadata
            result["metadata"] = {
                "live_data": False,
                "games_filter": games,
                "tournaments_filter": tournaments,
                "timezone": timezone,
                "day_filter": day if day else None,
                "fetched_at": datetime.now(ZoneInfo('UTC')).isoformat()
            }
            return jsonify(result)

    except ValueError as ve:
        return jsonify({
            "error": "Invalid parameter value",
            "message": str(ve),
            "type": "validation_error"
        }), 400

    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "type": "server_error"
        }), 500