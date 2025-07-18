import requests, random
from bs4 import BeautifulSoup
from app.utils import convert_timestamp_to_eest
from app.db import get_connection

BASE_URL = "https://liquipedia.net"
USER_AGENTS = ['Mozilla/5.0', 'Safari/537.36']

session = requests.Session()
session.headers.update({
    'User-Agent': random.choice(USER_AGENTS),
    'Referer': 'https://www.google.com/',
})


def scrape_matches(game: str = "dota2"):
    url = f"{BASE_URL}/{game}/api.php"
    params = {
        'action': 'parse',
        'page': "Liquipedia:Matches",
        'format': 'json',
        'prop': 'text'
    }
    response = session.get(url, params=params)
    soup = BeautifulSoup(response.json()['parse']['text']['*'], 'html.parser')
    
    matches_data = {}

    for section in soup.select('div[data-toggle-area-content]'):
        status = "Upcoming" if section.get('data-toggle-area-content') == "1" else "Completed"
        
        for match in section.select('.match'):
            team1 = match.select_one('.team-left .team-template-text a')
            team2 = match.select_one('.team-right .team-template-text a')
            score_spans = [s.text.strip() for s in match.select('.versus-upper span') if s.text.strip()]
            score = ":".join(score_spans) if len(score_spans) >= 2 else ""
            match_time_el = match.select_one(".timer-object")
            match_time = convert_timestamp_to_eest(int(match_time_el['data-timestamp'])) if match_time_el else "N/A"
            fmt = match.select_one('.versus-lower abbr')
            tournament = match.select_one('.match-tournament .tournament-name a')
            bracket = match.select_one('.bracket-header span') or match.select_one('.bracket-header')

            match_obj = {
                "team1": team1.text.strip() if team1 else "N/A",
                "team2": team2.text.strip() if team2 else "N/A",
                "score": score,
                "match_time": match_time,
                "format": fmt.text.strip() if fmt else "N/A",
                "stream_link": "N/A",  # Optional
                "group": bracket.text.strip() if bracket else None,
                "tournament": tournament.text.strip() if tournament else "Unknown",
                "status": status,
                "game": game
            }

            matches_data.setdefault(status, {}).setdefault(match_obj['tournament'], {"matches": []})["matches"].append(match_obj)

    return matches_data


def save_matches_to_db(game: str, matches_data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM matches WHERE game = ?", (game,))

    for status, tournaments in matches_data.items():
        for tournament_name, tournament_info in tournaments.items():
            for match in tournament_info["matches"]:
                cursor.execute('''
                    INSERT INTO matches (
                        game, status, tournament, team1, team2, score, match_time, format, stream_link, match_group
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    game,
                    status,
                    tournament_name,
                    match.get("team1"),
                    match.get("team2"),
                    match.get("score"),
                    match.get("match_time"),
                    match.get("format"),
                    match.get("stream_link"),
                    match.get("group")
                ))
    conn.commit()
    conn.close()

def get_matches_by_filters(games=[], tournaments=[], live=False, page=1, per_page=10):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM matches WHERE 1=1"
    params = []

    if games:
        query += f" AND game IN ({','.join(['?'] * len(games))})"
        params.extend(games)

    if tournaments:
        query += f" AND tournament_name IN ({','.join(['?'] * len(tournaments))})"
        params.extend(tournaments)

    if live:
        query += " AND status = 'Not Started'"

    query += " ORDER BY id ASC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    cursor.execute(query, params)
    matches = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM matches WHERE 1=1", ()) 
    total = cursor.fetchone()[0]

    keys = [column[0] for column in cursor.description]
    result = [dict(zip(keys, row)) for row in matches]

    conn.close()
    return result, total

def get_matches_from_db(game: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE game = ?", (game,))
    rows = cursor.fetchall()
    conn.close()

    result = {}
    for row in rows:
        result.setdefault(row["status"], {}).setdefault(row["tournament"], {"matches": []})["matches"].append({
            "team1": row["team1"],
            "team2": row["team2"],
            "score": row["score"],
            "match_time": row["match_time"],
            "format": row["format"],
            "stream_link": row["stream_link"],
            "group": row["match_group"]
        })

    return result

def get_matches_paginated(
    games: list = [],
    tournaments: list = [],
    live: bool = False,
    page: int = 1,
    per_page: int = 10
):
    conn = get_connection()
    cursor = conn.cursor()

    # Build filter conditions
    where_clauses = []
    params = []

    if games:
        where_clauses.append(f"game IN ({','.join(['?'] * len(games))})")
        params.extend(games)

    if tournaments:
        where_clauses.append(f"tournament IN ({','.join(['?'] * len(tournaments))})")
        params.extend(tournaments)

    if live:
        where_clauses.append("status = 'Not Started'")

    where_sql = " AND ".join(where_clauses)
    if where_sql:
        where_sql = "WHERE " + where_sql

    # Get total count of unique tournaments
    cursor.execute(f"""
        SELECT COUNT(DISTINCT tournament)
        FROM matches
        {where_sql}
    """, params)
    total_tournaments = cursor.fetchone()[0]

    # Get paginated tournament names
    cursor.execute(f"""
        SELECT DISTINCT tournament
        FROM matches
        {where_sql}
        ORDER BY tournament
        LIMIT ? OFFSET ?
    """, params + [per_page, (page - 1) * per_page])
    tournament_names = [row[0] for row in cursor.fetchall()]

    if not tournament_names:
        conn.close()
        return {
            "page": page,
            "per_page": per_page,
            "total": total_tournaments,
            "tournaments": []
        }

    # Get matches for the selected tournaments
    match_params = list(params) + tournament_names
    match_clause = f"{where_sql} AND tournament IN ({','.join(['?'] * len(tournament_names))})" if where_sql else f"WHERE tournament IN ({','.join(['?'] * len(tournament_names))})"

    cursor.execute(f"""
        SELECT *
        FROM matches
        {match_clause}
        ORDER BY tournament, match_time
    """, match_params)
    matches = cursor.fetchall()
    keys = [column[0] for column in cursor.description]
    matches_data = [dict(zip(keys, row)) for row in matches]
    conn.close()

    # Organize and sort matches
    tournaments_map = {}
    for match in matches_data:
        tournament_name = match['tournament']
        if tournament_name not in tournaments_map:
            tournaments_map[tournament_name] = {
                "tournament_name": tournament_name,
                "tournament_icon": f"{BASE_URL}/commons/images/thumb/liquipedia_logo.png/600px-liquipedia_logo.png",
                "tournament_link": f"{BASE_URL}/{match['game']}/tournaments/{tournament_name.replace(' ', '_')}",
                "games": []
            }

        # Group by game
        game_entry = next((g for g in tournaments_map[tournament_name]["games"] if g["game"] == match["game"]), None)
        if not game_entry:
            game_entry = {
                "game": match["game"],
                "matches": []
            }
            tournaments_map[tournament_name]["games"].append(game_entry)

        game_entry["matches"].append({
            "team1": match["team1"],
            "team2": match["team2"],
            "score": match["score"],
            "match_time": match["match_time"],
            "format": match["format"],
            "stream_link": match["stream_link"],
            "group": match["match_group"],
            "status": match["status"]
        })

    # Sort games and matches
    for tournament in tournaments_map.values():
        for game_entry in tournament["games"]:
            game_entry["matches"].sort(key=lambda m: m["match_time"])
        tournament["games"] = sorted(tournament["games"], key=lambda g: g["game"])

    return {
        "page": page,
        "per_page": per_page,
        "total": total_tournaments,
        "tournaments": list(tournaments_map.values())
    }
