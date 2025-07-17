from flask import Blueprint, request, jsonify
from app.game_matches_init_db import get_connection, init_game_matches_db
from app.crud.game_matches_crud import get_grouped_matches
from app.game_matches import scrape_matches
import json

game_matches_bp = Blueprint('game_matches', __name__)

@game_matches_bp.route('/game_matches', methods=['GET'])
def game_matches():
    # Initialize game matches tables
    init_game_matches_db()

    game = request.args.get('game')
    day = request.args.get('day')
    live = request.args.get('live', 'false').lower() == 'true'
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    if live and not game:
        return jsonify({"error": "Game parameter is required when live=true"}), 400

    conn = get_connection()

    if live:
        match_data = scrape_matches(game)
        for status, tournaments in match_data.items():
            for tournament_name, tournament_data in tournaments.items():
                tournament_link = tournament_data["tournament_link"]
                tournament_id = insert_or_update_tournament(
                    conn, game, tournament_name, tournament_link, tournament_data["tournament_icon"]
                )
                for match in tournament_data["matches"]:
                    match_id = match["match_id"]
                    if match_id:
                        insert_or_update_match(
                            conn, tournament_id, match_id, status, match["team1"], match["team1_url"],
                            match["logo1_light"], match["logo1_dark"], match["team2"], match["team2_url"],
                            match["logo2_light"], match["logo2_dark"], match["timestamp"], match["match_time"],
                            match["format"], match["score"], json.dumps(match["stream_link"]), match["details_link"],
                            match.get("group")
                        )

    grouped_matches, total = get_grouped_matches(conn, game=game, day=day, page=page, per_page=per_page)
    response = {
        "tournaments": grouped_matches,
        "total": total,
        "page": page,
        "per_page": per_page
    }
    return jsonify(response)

def insert_or_update_tournament(conn, game, name, link, icon):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tournaments (game, name, link, icon)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(link) DO UPDATE SET
            game = excluded.game,
            name = excluded.name,
            icon = excluded.icon,
            updated_at = CURRENT_TIMESTAMP
    ''', (game, name, link, icon))
    conn.commit()
    cursor.execute("SELECT id FROM tournaments WHERE link = ?", (link,))
    return cursor.fetchone()['id']

def insert_or_update_match(conn, tournament_id, match_id, status, team1, team1_url, logo1_light, logo1_dark,
                           team2, team2_url, logo2_light, logo2_dark, timestamp, match_time, format_, score,
                           stream_links, details_link, group_name):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO matches (tournament_id, match_id, status, team1, team1_url, logo1_light, logo1_dark,
                             team2, team2_url, logo2_light, logo2_dark, timestamp, match_time, format, score,
                             stream_links, details_link, group_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(match_id) DO UPDATE SET
            status = excluded.status,
            team1 = excluded.team1,
            team1_url = excluded.team1_url,
            logo1_light = excluded.logo1_light,
            logo1_dark = excluded.logo1_dark,
            team2 = excluded.team2,
            team2_url = excluded.team2_url,
            logo2_light = excluded.logo2_light,
            logo2_dark = excluded.logo2_dark,
            timestamp = excluded.timestamp,
            match_time = excluded.match_time,
            format = excluded.format,
            score = excluded.score,
            stream_links = excluded.stream_links,
            details_link = excluded.details_link,
            group_name = excluded.group_name,
            updated_at = CURRENT_TIMESTAMP
    ''', (tournament_id, match_id, status, team1, team1_url, logo1_light, logo1_dark,
          team2, team2_url, logo2_light, logo2_dark, timestamp, match_time, format_, score,
          stream_links, details_link, group_name))
    conn.commit()