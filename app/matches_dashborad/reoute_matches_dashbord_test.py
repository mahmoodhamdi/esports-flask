from flask import Blueprint, request, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from app.matches_dashborad.match_model import MatchModel
from app.matches_dashborad.matches_dashbord_test import save_live_matches_to_db, validate_match_data
from app.matches_mohamed import get_matches_paginated

matches_bp = Blueprint('matches', __name__)

SUPPORTED_TIMEZONES = [
    'Africa/Cairo', 'Europe/London', 'Europe/Berlin', 'Europe/Athens',
    'America/New_York', 'America/Los_Angeles', 'America/Chicago', 'America/Denver',
    'Asia/Tokyo', 'Asia/Seoul', 'Asia/Singapore', 'Asia/Kolkata',
    'Australia/Sydney', 'UTC'
]

@matches_bp.route("/matches_mohamed", methods=["GET", "POST"])
def get_matches():
    try:
        live = request.args.get("live", "false").lower() == "true"
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        day = request.args.get("day")
        timezone = request.args.get("timezone", "UTC")

        if page < 1:
            return jsonify({"error": "Page number must be greater than 0"}), 400
        if per_page < 1 or per_page > 100:
            return jsonify({"error": "per_page must be between 1 and 100"}), 400
        if day:
            try:
                datetime.strptime(day, "%Y-%m-%d")
            except ValueError:
                return jsonify({
                    "error": "Invalid day format. Expected format: YYYY-MM-DD",
                    "example": "2025-07-24"
                }), 400
        try:
            ZoneInfo(timezone)
        except Exception:
            return jsonify({
                "error": f"Invalid timezone: {timezone}",
                "message": "Please use IANA timezone format",
                "examples": SUPPORTED_TIMEZONES
            }), 400

        if live and request.method != "POST":
            return jsonify({"error": "Sending live matches with data requires POST request"}), 405
        if not live and request.method != "GET":
            return jsonify({"error": "Fetching matches requires GET request"}), 405

        if live:
            game = request.args.get("game")
            if not game:
                return jsonify({
                    "error": "Missing required parameter: game",
                    "message": "When live=true, you must specify a game"
                }), 400

            data = request.get_json()
            if not data:
                return jsonify({
                    "error": "Missing JSON body",
                    "message": "You must send match data in request body when live=true"
                }), 400

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

                missing = [field for field in required_fields if field not in item]
                if missing:
                    validation_errors.append({
                        "match_index": i,
                        "error": f"Missing required fields: {', '.join(missing)}"
                    })
                    continue

                is_valid, reason = validate_match_data({
                    "team1": item["team1"],
                    "team2": item["team2"]
                })
                if not is_valid:
                    validation_errors.append({
                        "match_index": i,
                        "error": f"Invalid match data: {reason}",
                        "teams": f"{item['team1']} vs {item['team2']}"
                    })
                    continue

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
                    "error": "Validation failed for some matches",
                    "validation_errors": validation_errors,
                    "valid_matches": len(matches),
                    "invalid_matches": len(validation_errors)
                }), 400

            save_result = {"saved": 0, "skipped": 0, "status_distribution": {"Upcoming": 0, "live": 0, "Completed": 0}}
            if matches:
                print(f"💾 Saving {len(matches)} manually submitted matches for {game}...")
                save_result = save_live_matches_to_db(game, matches)
                print(f"✅ Save result: {save_result}")

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
                "submitted_at": datetime.now(ZoneInfo('UTC')).isoformat(),
                "day_filter": day if day else None,
                "save_summary": save_result
            }
            return jsonify(result)

        else:
            games = request.args.getlist("game")
            tournaments = request.args.getlist("tournament")

            print(f"📊 Fetching matches from database...")
            if games: print(f"   Games filter: {games}")
            if tournaments: print(f"   Tournaments filter: {tournaments}")
            if day: print(f"   Day filter: {day}")
            if timezone: print(f"   Timezone: {timezone}")

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
