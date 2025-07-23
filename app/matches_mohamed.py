import requests, random, json, os, hashlib
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from app.utils import clean_liquipedia_url, convert_timestamp_to_eest ,BASE_URL
from app.db import get_connection
  

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; rv:125.0) Gecko/20100101 Firefox/125.0'
]

session = requests.Session()
session.headers.update({
    'User-Agent': random.choice(USER_AGENTS),
    'Referer': 'https://www.google.com/',
    'Accept-Language': 'en-US,en;q=0.9',
    'DNT': '1',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'X-Requested-With': 'XMLHttpRequest'
})
def parse_match_date(match_time_str):
    try:
        if match_time_str == "N/A" or not match_time_str:
            return None
        date_part = match_time_str.split(" - ")[0]
        return datetime.strptime(date_part, "%B %d, %Y").date()
    except:
        return None




def convert_timestamp_to_eest(timestamp: int) -> str:
    dt_utc = datetime.utcfromtimestamp(timestamp).replace(tzinfo=ZoneInfo("UTC"))
    dt_eest = dt_utc.astimezone(ZoneInfo("Europe/Athens"))  # EEST (UTC+3)
    return dt_eest.strftime("%B %d, %Y - %H:%M EEST")


def extract_team_logos(team_side_element):
    light_tag = team_side_element.select_one('.team-template-lightmode img')
    dark_tag = team_side_element.select_one('.team-template-darkmode img')
    fallback_tag = team_side_element.select_one('.team-template-image-icon img')
    flag_tag = team_side_element.select_one('.flag img')

    def get_src(tag):
        return f"{BASE_URL}{tag['src']}" if tag and tag.has_attr("src") else "N/A"

    
    logo_light = (
        get_src(light_tag)
        if light_tag else
        get_src(fallback_tag)
        if fallback_tag else
        get_src(flag_tag)
    )

    logo_dark = (
        get_src(dark_tag)
        if dark_tag else
        get_src(fallback_tag)
        if fallback_tag else
        get_src(flag_tag)
    )

    return logo_light, logo_dark

def extract_tournament_icon(match):
    dark_icon = match.select_one('.match-info-tournament .darkmode img')
    light_icon = match.select_one('.match-info-tournament .lightmode img')
    any_icon = match.select_one('.match-info-tournament img')

    def get_src(tag):
        return f"{BASE_URL}{tag['src']}" if tag and tag.has_attr('src') else ""

    return get_src(dark_icon) or get_src(light_icon) or get_src(any_icon) or "N/A"

def scrape_matches(game: str = "valorant"):
    API_URL = f"{BASE_URL}/{game}/api.php"
    PAGE = "Main_Page"

    params = {'action': 'parse', 'page': PAGE, 'format': 'json', 'prop': 'text'}
    response = session.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    html_content = response.json()['parse']['text']['*']
    soup = BeautifulSoup(html_content, "html.parser")

    data = {"Upcoming": {}, "Completed": {}}

    sections = soup.select('div[data-toggle-area-content]')
    for section in sections:
        section_type = section.get('data-toggle-area-content')
        status = "Upcoming" if section_type == "1" else "Completed" if section_type == "2" else "Other"
        if status not in data:
            continue

        for match in section.select('.match-info'):
            team1 = match.select_one('.match-info-header-opponent-left .name a')
            team2 = match.select_one('.match-info-header-opponent:not(.match-info-header-opponent-left) .name a')

            team1_element = match.select_one('.match-info-header-opponent-left')
            team2_element = match.select_one('.match-info-header-opponent:not(.match-info-header-opponent-left)')

            team1_url_raw = f"{BASE_URL}{team1['href']}" if team1 and team1.has_attr('href') else ""
            team2_url_raw = f"{BASE_URL}{team2['href']}" if team2 and team2.has_attr('href') else ""

            team1_url = clean_liquipedia_url(team1_url_raw)
            team2_url = clean_liquipedia_url(team2_url_raw)

            logo1_light, logo1_dark = extract_team_logos(team1_element)
            logo2_light, logo2_dark = extract_team_logos(team2_element)

            fmt = match.select_one('.match-info-header-scoreholder-lower')
            score_spans = [s.text.strip() for s in match.select('.match-info-header-scoreholder-score')]
            score = ":".join(score_spans) if len(score_spans) == 2 else ""

            timer_span = match.select_one(".timer-object")
            timestamp = timer_span.get("data-timestamp") if timer_span else None
            match_time = convert_timestamp_to_eest(int(timestamp)) if timestamp else "N/A"

            stream_links = []
            for a in match.select('.match-info-links a'):
                href = a.get('href', '')
                full_link = href if href.startswith("http") else f"{BASE_URL}{href}"
                stream_links.append(full_link)

            details_link = next((f"{BASE_URL}{a['href']}" for a in match.select('.match-info-links a')
                                 if 'match:' in a['href'].lower()), "N/A")

            tournament_tag = match.select_one('.match-info-tournament .tournament-name a')
            tournament_name = tournament_tag.text.strip() if tournament_tag else "Unknown Tournament"

            if tournament_name not in data[status]:
                data[status][tournament_name] = {
                    "tournament": tournament_name,
                    "tournament_link": f"{BASE_URL}{tournament_tag['href']}" if tournament_tag else "",
                    "tournament_icon": extract_tournament_icon(match),
                    "matches": []
                }

            match_info = {
                "team1": team1.text.strip() if team1 else "N/A",
                "team1_url": team1_url,
                "logo1_light": logo1_light,
                "logo1_dark": logo1_dark,
                "team2": team2.text.strip() if team2 else "N/A",
                "team2_url": team2_url,
                "logo2_light": logo2_light,
                "logo2_dark": logo2_dark,
                "match_time": match_time,
                "format": fmt.text.strip() if fmt else "N/A",
                "score": score,
                "stream_link": stream_links,
                "details_link": details_link,
                "group": (match.select_one('.bracket-header span') or match.select_one('.bracket-header')).text.strip()
                if match.select_one('.bracket-header') else None
            }

            data[status][tournament_name]["matches"].append(match_info)

    return data


def calculate_hash(obj):
    return hashlib.md5(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def update_file_if_changed(game, new_data):
    filename = f"{game}_matches.json"
    old_data = {}
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            old_data = json.load(f)

    if calculate_hash(old_data) != calculate_hash(new_data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Updated {filename}")
    else:
        print("🟡 No changes detected.")


def save_matches_to_db(game: str, matches_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM matches WHERE game = ?", (game,))
    for status, tournaments in matches_data.items():
        for tournament_name, tournament_info in tournaments.items():
            t_link = tournament_info.get("tournament_link", "")
            t_icon = tournament_info.get("tournament_icon", "")
            for match in tournament_info["matches"]:
                cursor.execute('''
                    INSERT INTO matches (
                        game, status, tournament, tournament_link, tournament_icon,
                        team1, team1_url, logo1_light, logo1_dark,
                        team2, team2_url, logo2_light, logo2_dark,
                        score, match_time, format, stream_links, details_link, match_group
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    game, status, tournament_name, t_link, t_icon,
                    match.get("team1"), match.get("team1_url"),
                    match.get("logo1_light"), match.get("logo1_dark"),
                    match.get("team2"), match.get("team2_url"),
                    match.get("logo2_light"), match.get("logo2_dark"),
                    match.get("score"), match.get("match_time"),
                    match.get("format"), json.dumps(match.get("stream_link", [])),
                    match.get("details_link"), match.get("group")
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
        query += f" AND tournament IN ({','.join(['?'] * len(tournaments))})"
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
    day: str = None,  # New parameter: format "YYYY-MM-DD"
    page: int = 1,
    per_page: int = 10
):
    conn = get_connection()
    cursor = conn.cursor()

    # Build WHERE conditions
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

    # Add day filter
    if day:
        try:
            # Parse the day parameter (expected format: YYYY-MM-DD)
            filter_date = datetime.strptime(day, "%Y-%m-%d").date()
            
            # Get all matches and filter by date in Python (since SQLite doesn't have native date parsing for our format)
            where_clauses.append("match_time != 'N/A' AND match_time IS NOT NULL")
            
        except ValueError:
            # Invalid date format, ignore the filter
            pass

    where_sql = " AND ".join(where_clauses)
    if where_sql:
        where_sql = "WHERE " + where_sql

    # First, get all matches that match the basic filters
    cursor.execute(f"""
        SELECT *
        FROM matches
        {where_sql}
        ORDER BY tournament, match_time
    """, params)

    all_matches = cursor.fetchall()
    keys = [column[0] for column in cursor.description]
    matches_data = [dict(zip(keys, row)) for row in all_matches]

    # Apply day filter in Python if specified
    if day:
        try:
            filter_date = datetime.strptime(day, "%Y-%m-%d").date()
            filtered_matches = []
            
            for match in matches_data:
                match_date = parse_match_date(match.get('match_time'))
                if match_date and match_date == filter_date:
                    filtered_matches.append(match)
            
            matches_data = filtered_matches
        except ValueError:
            # Invalid date format, use all matches
            pass

    # Group matches by tournament
    tournaments_map = {}
    for match in matches_data:
        tournament_name = match['tournament']
        if tournament_name not in tournaments_map:
            tournaments_map[tournament_name] = {
                "tournament_name": tournament_name,
                "tournament_icon": match.get("tournament_icon", ""),
                "tournament_link": match.get("tournament_link", ""),
                "games": []
            }

        game_entry = next((g for g in tournaments_map[tournament_name]["games"] if g["game"] == match["game"]), None)
        if not game_entry:
            game_entry = {
                "game": match["game"],
                "matches": []
            }
            tournaments_map[tournament_name]["games"].append(game_entry)

        game_entry["matches"].append({
            "team1": match["team1"],
            "team1_url": match.get("team1_url"),
            "logo1_light": match["logo1_light"],
            "logo1_dark": match["logo1_dark"],
            "team2": match["team2"],
            "team2_url": match.get("team2_url"),
            "logo2_light": match["logo2_light"],
            "logo2_dark": match["logo2_dark"],
            "score": match["score"],
            "match_time": match["match_time"],
            "format": match["format"],
            "stream_link": json.loads(match["stream_links"]) if match.get("stream_links") else [],
            "details_link": match.get("details_link"),
            "group": match["match_group"],
            "status": match["status"]
        })

    # Apply pagination to tournaments
    total_tournaments = len(tournaments_map)
    tournament_list = list(tournaments_map.values())
    
    # Sort tournaments
    priority = [
        'EWC 2025',
        'Esports World Cup 2025',
        'Esports World Cup 2025 - BO6',
        'Esports World Cup 2025 - Warzone',
        'Honor of Kings World Cup 2025',
        'PUBG Mobile World Cup 2025',
    ]
    
    tournament_list.sort(
        key=lambda t: (priority.index(t["tournament_name"]) if t["tournament_name"] in priority else float('inf'))
    )

    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_tournaments = tournament_list[start_idx:end_idx]

    # Sort matches within each tournament
    for tournament in paginated_tournaments:
        for game_entry in tournament["games"]:
            game_entry["matches"].sort(key=lambda m: m["match_time"])
        tournament["games"] = sorted(tournament["games"], key=lambda g: g["game"])

    conn.close()

    return {
        "page": page,
        "per_page": per_page,
        "total": total_tournaments,
        "tournaments": paginated_tournaments
    }