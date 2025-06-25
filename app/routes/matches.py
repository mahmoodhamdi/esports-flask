from flask import Blueprint, request, jsonify
from app.matches import fetch_group_matches, save_group_matches_to_db, update_group_matches, delete_group_matches, get_group_matches
from app.utils import sanitize_input, is_valid_date
from datetime import datetime
import re

matches_bp = Blueprint("group_stage_matches", __name__)

@matches_bp.route("/fetch-and-store", methods=["POST"])
def fetch_and_store_matches():
    """Fetch and store group stage matches with optional filters"""
    game = sanitize_input(request.args.get("game"), max_length=50)
    tournament = sanitize_input(request.args.get("tournament"), max_length=100)
    start_date = sanitize_input(request.args.get("start_date"), max_length=10)
    end_date = sanitize_input(request.args.get("end_date"), max_length=10)
    group_name = sanitize_input(request.args.get("group_name"), max_length=50)

    if not game or not tournament:
        return jsonify({"error": "Missing game or tournament parameter"}), 400

    if start_date and not is_valid_date(start_date):
        return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    if end_date and not is_valid_date(end_date):
        return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    if start_date and end_date and start_date > end_date:
        return jsonify({"error": "start_date cannot be later than end_date"}), 400
    if group_name and not re.match(r'^[A-Za-z0-9\s-]+$', group_name):
        return jsonify({"error": "Invalid group_name format. Use alphanumeric, spaces, or hyphens only"}), 400

    try:
        result = fetch_group_matches(game, tournament)
        if result["status"] != "ok":
            return jsonify({"status": result["status"], "message": "No matches found or page missing"}), 404

        filtered_matches = filter_matches(result["matches"], start_date, end_date, group_name)
        if not filtered_matches:
            return jsonify({"status": "no_matches", "message": "No matches found with specified filters"}), 404

        save_group_matches_to_db(game, tournament, filtered_matches)
        total_matches = sum(len(v) for v in filtered_matches.values())

        return jsonify({
            "message": f"{total_matches} matches saved to database.",
            "groups": list(filtered_matches.keys()),
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "group_name": group_name
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@matches_bp.route("/matches", methods=["GET"])
def get_matches():
    """Retrieve matches with optional filters"""
    game = sanitize_input(request.args.get("game"), max_length=50)
    tournament = sanitize_input(request.args.get("tournament"), max_length=100)
    group_name = sanitize_input(request.args.get("group_name"), max_length=50)
    start_date = sanitize_input(request.args.get("start_date"), max_length=10)
    end_date = sanitize_input(request.args.get("end_date"), max_length=10)

    if not game or not tournament:
        return jsonify({"error": "Missing game or tournament parameter"}), 400

    try:
        matches = get_group_matches(game, tournament, group_name, start_date, end_date)
        if not matches:
            return jsonify({"status": "no_matches", "message": "No matches found"}), 404

        return jsonify({
            "message": f"{len(matches)} matches retrieved.",
            "matches": matches
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@matches_bp.route("/update", methods=["PUT"])
def update_matches():
    """Update a specific match"""
    data = request.get_json()
    game = sanitize_input(data.get("game"), max_length=50)
    tournament = sanitize_input(data.get("tournament"), max_length=100)
    group_name = sanitize_input(data.get("group_name"), max_length=50)
    match_id = data.get("match_id")

    if not all([game, tournament, group_name, match_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        update_data = {
            "team1_name": sanitize_input(data.get("team1_name"), max_length=100),
            "team1_logo": sanitize_input(data.get("team1_logo"), max_length=255),
            "team2_name": sanitize_input(data.get("team2_name"), max_length=100),
            "team2_logo": sanitize_input(data.get("team2_logo"), max_length=255),
            "match_time": sanitize_input(data.get("match_time"), max_length=50),
            "score": sanitize_input(data.get("score"), max_length=50)
        }

        if update_group_matches(game, tournament, group_name, match_id, update_data):
            return jsonify({"message": "Match updated successfully"})
        else:
            return jsonify({"error": "Match not found or update failed"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@matches_bp.route("/delete", methods=["DELETE"])
def delete_matches():
    """Delete matches with optional filters"""
    game = sanitize_input(request.args.get("game"), max_length=50)
    tournament = sanitize_input(request.args.get("tournament"), max_length=100)
    group_name = sanitize_input(request.args.get("group_name"), max_length=50)
    match_id = request.args.get("match_id")

    if not game or not tournament:
        return jsonify({"error": "Missing game or tournament parameter"}), 400

    try:
        deleted = delete_group_matches(game, tournament, group_name, match_id)
        if deleted:
            return jsonify({"message": f"{deleted} match(es) deleted successfully"})
        else:
            return jsonify({"error": "No matches found to delete"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def filter_matches(matches: dict, start_date: str = None, end_date: str = None, group_name: str = None) -> dict:
    """Filter matches by date range and group name"""
    if not matches:
        return {}

    filtered = {}
    start = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

    for group, match_list in matches.items():
        if group_name and group != group_name:
            continue

        filtered_matches = []
        for match in match_list:
            match_time = match.get("MatchTime")
            if match_time == "N/A":
                filtered_matches.append(match)
                continue

            try:
                match_date = datetime.strptime(match_time.split()[0], '%Y-%m-%d')
                if start and match_date < start:
                    continue
                if end and match_date > end:
                    continue
                filtered_matches.append(match)
            except ValueError:
                filtered_matches.append(match)

        if filtered_matches:
            filtered[group] = filtered_matches

    return filtered