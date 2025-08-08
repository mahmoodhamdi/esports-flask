import re
from flask import Blueprint, request, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.parser import isoparse
from app.matches_dashborad.match_model import MatchModel
from app.matches_dashborad.matches_dashbord_test import save_live_matches_to_db, update_match_in_db, validate_match_data
from app.matches_dashborad.matches_dashbord_test import get_matches_paginated

matches_bp = Blueprint('matches', __name__)
ISO_REGEX = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)$'

SUPPORTED_TIMEZONES = [
    'Africa/Cairo', 'Europe/London', 'Europe/Berlin', 'Europe/Athens',
    'America/New_York', 'America/Los_Angeles', 'America/Chicago', 'America/Denver',
    'Asia/Tokyo', 'Asia/Seoul', 'Asia/Singapore', 'Asia/Kolkata',
    'Australia/Sydney', 'UTC'
]
@matches_bp.route("/matches_mohamed", methods=["GET", "POST", "PATCH"])
def handle_matches():
    try:
        method = request.method

        if method == "GET":
            # 🟩 جلب المباريات
            live = request.args.get("live", "false").lower() == "true"
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 10))
            day = request.args.get("day")
            timezone = request.args.get("timezone", "UTC")
            games = request.args.getlist("game")
            tournaments = request.args.getlist("tournament")

            # تحقق من صحة البيانات
            if day:
                try:
                    datetime.strptime(day, "%Y-%m-%d")
                except ValueError:
                    return jsonify({
                        "error": "Invalid day format. Expected format: YYYY-MM-DD"
                    }), 400

            if timezone not in SUPPORTED_TIMEZONES:
                return jsonify({
                    "error": f"Invalid timezone: {timezone}",
                    "examples": SUPPORTED_TIMEZONES
                }), 400

            result = get_matches_paginated(
                games=games,
                tournaments=tournaments,
                live=False,
                day=day,
                page=page,
                per_page=per_page,
                timezone=timezone
            )
            result["metadata"] = {
                "method": "GET",
                "timezone": timezone,
                "day_filter": day,
                "fetched_at": datetime.now(ZoneInfo("UTC")).isoformat()
            }
            return jsonify(result)
# !--------------------ADD MATCH-----------------------------
        elif method == "POST":
            live = request.args.get("live", "false").lower() == "true"
            if not live:
                return jsonify({
                    "error": "POST only supported for live=true"
                }), 400

            game = request.args.get("game")
            if not game:
                return jsonify({
                    "error": "Missing game in query"
                }), 400

            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing JSON body"}), 400

            if isinstance(data, dict):
                data = [data]

            matches = []
            validation_errors = []

            for i, item in enumerate(data):
                required_fields = [
                    "game", "status", "tournament", "tournament_link",
                    "tournament_icon", "team1", "team1_url", "logo1_light",
                    "logo1_dark", "team2", "team2_url", "logo2_light",
                    "logo2_dark", "score", "match_time", "format", "details_link"
                ]

                missing = [f for f in required_fields if f not in item]
                if missing:
                    validation_errors.append({
                        "match_index": i,
                        "error": f"Missing required fields: {', '.join(missing)}"
                    })
                    continue

                # ✅ تحقق من match_time
                try:
                    match_time_str = item["match_time"]
                    parsed_time = isoparse(match_time_str)
                    
                    if parsed_time.tzinfo is None:
                        raise ValueError("match_time must include timezone info (e.g. +00:00 or Z)")
                    
                    if not re.match(ISO_REGEX, match_time_str):
                        raise ValueError("match_time format must match ISO8601 with timezone")

                except Exception as e:
                    validation_errors.append({
                        "match_index": i,
                        "error": f"Invalid match_time format: {str(e)}"
                    })
                    continue                # ✅ تحقق من صحة أسماء الفرق
                is_valid, reason = validate_match_data({
                    "team1": item["team1"],
                    "team2": item["team2"]
                })
                if not is_valid:
                    validation_errors.append({
                        "match_index": i,
                        "error": f"Invalid match data: {reason}"
                    })
                    continue

                # ✅ إنشاء الماتش
                match = MatchModel(
                    game=item["game"],
                    status=item["status"],
                    tournament=item["tournament"],
                    tournament_link=item["tournament_link"],
                    tournament_icon=item["tournament_icon"],
                    team1=item["team1"],
                    team1_url=item["team1_url"],
                    logo1_light=item["logo1_light"],
                    logo1_dark=item["logo1_dark"],
                    team2=item["team2"],
                    team2_url=item["team2_url"],
                    logo2_light=item["logo2_light"],
                    logo2_dark=item["logo2_dark"],
                    score=item["score"],
                    match_time=item["match_time"],
                    format=item["format"],
                    stream_links=item.get("stream_links", []),
                    details_link=item["details_link"],
                    match_group=item.get("match_group")
                )
                matches.append(match)

            if validation_errors:
                return jsonify({
                    "error": "Validation failed",
                    "validation_errors": validation_errors
                }), 400

            save_result = save_live_matches_to_db(game, matches)

            return jsonify({
                "message": "Matches saved successfully",
                "save_result": save_result,
                "saved_at": datetime.now(ZoneInfo("UTC")).isoformat()
            })
# !--------------------UPDATE MATCH-----------------------------
        elif method == "PATCH":
            
            uid = request.args.get("uid")
            if not uid:
                return jsonify({"error": "Missing uid parameter in query"}), 400

            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            result = update_match_in_db(uid, data)
            if "error" in result:
                return jsonify(result), 404 if result["error"] == "Match not found" else 400

            return jsonify({
                "message": "Match updated successfully",
                "updated_data": result
            })

        else:
            return jsonify({"error": "Method not allowed"}), 405

    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500
