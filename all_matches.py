import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib
import random
from datetime import datetime
from zoneinfo import ZoneInfo

BASE_URL = "https://liquipedia.net"

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


def convert_timestamp_to_eest(timestamp: int) -> str:
    dt_utc = datetime.utcfromtimestamp(timestamp).replace(tzinfo=ZoneInfo("UTC"))
    dt_eest = dt_utc.astimezone(ZoneInfo("Europe/Athens"))  # EEST (UTC+3)
    return dt_eest.strftime("%B %d, %Y - %H:%M EEST")


def extract_team_logos(team_side_element):
    light_tag = team_side_element.select_one('.team-template-lightmode img')
    dark_tag = team_side_element.select_one('.team-template-darkmode img')
    fallback_tag = team_side_element.select_one('.team-template-image-icon img')

    logo_light = f"{BASE_URL}{light_tag['src']}" if light_tag else (
        f"{BASE_URL}{fallback_tag['src']}" if fallback_tag else "N/A"
    )
    logo_dark = f"{BASE_URL}{dark_tag['src']}" if dark_tag else (
        f"{BASE_URL}{fallback_tag['src']}" if fallback_tag else "N/A"
    )
    return logo_light, logo_dark


def scrape_matches(game: str = "dota2"):
    API_URL = f"{BASE_URL}/{game}/api.php"
    PAGE = "Liquipedia:Matches"

    params = {
        'action': 'parse',
        'page': PAGE,
        'format': 'json',
        'prop': 'text'
    }

    response = session.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    html_content = response.json()['parse']['text']['*']
    soup = BeautifulSoup(html_content, "html.parser")

    data = {
        "Upcoming": {},
        "Completed": {}
    }

    sections = soup.select('div[data-toggle-area-content]')
    for section in sections:
        section_type = section.get('data-toggle-area-content')
        status = "Upcoming" if section_type == "1" else "Completed" if section_type == "2" else "Other"
        if status not in data:
            continue

        for match in section.select('.match'):
            team1 = match.select_one('.team-left .team-template-text a')
            team2 = match.select_one('.team-right .team-template-text a')

            team1_element = match.select_one('.team-left')
            team1_url = f"{BASE_URL}{team1['href']}"if team1 and team1.has_attr('href') else ""
            team2_element = match.select_one('.team-right')
            team2_url = f"{BASE_URL}{team2['href']}"if team2 and team2.has_attr('href') else ""
            logo1_light, logo1_dark = extract_team_logos(team1_element)
            logo2_light, logo2_dark = extract_team_logos(team2_element)

            fmt = match.select_one('.versus-lower abbr')
            score_spans = [s.text.strip() for s in match.select('.versus-upper span') if s.text.strip()]
            score = ":".join(score_spans) if len(score_spans) >= 2 else ""

            timer_span = match.select_one(".timer-object")
            timestamp = timer_span.get("data-timestamp") if timer_span else None
            match_time = convert_timestamp_to_eest(int(timestamp)) if timestamp else "N/A"

            stream_links = []
            for a in match.select('.match-streams a'):
                if a.has_attr('href'):
                    stream_links.append(f"{BASE_URL}{a['href']}")
            
            details_div = match.select_one('.match-bottom-bar a')
            details_link = f"{BASE_URL}{details_div['href']}" if details_div and details_div.has_attr('href') else "N/A"


            tournament_tag = match.select_one('.match-tournament .tournament-name a')
            tournament_icon_tag = match.select_one('.match-tournament .tournament-icon img')

            tournament_name = tournament_tag.text.strip() if tournament_tag else "Unknown Tournament"
            if tournament_name not in data[status]:
                data[status][tournament_name] = {
                    "tournament": tournament_name,
                    "tournament_link": f"{BASE_URL}{tournament_tag['href']}" if tournament_tag else "",
                    "tournament_icon": f"{BASE_URL}{tournament_icon_tag['src']}" if tournament_icon_tag else "",
                    "matches": []
                }

            match_info = {
                "team1": team1.text.strip() if team1 else "N/A",
                'team1_url': team1_url,
                "logo1_light": logo1_light,
                "logo1_dark": logo1_dark,
                "team2": team2.text.strip() if team2 else "N/A",
                "team2_url" : team2_url,
                "logo2_light": logo2_light,
                "logo2_dark": logo2_dark,
                "match_time": match_time,
                "format": fmt.text.strip() if fmt else "N/A",
                "score": score,
                "stream_link": stream_links,
                "details_link": details_link
            }

            bracket_header = match.select_one('.bracket-header span') or match.select_one('.bracket-header')
            if bracket_header:
                match_info["group"] = bracket_header.text.strip()

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
        print(f"Updated {filename}")
    else:
        print("No changes detected.")


if __name__ == "__main__":
    game = "valorant"  
    match_data = scrape_matches(game)
    update_file_if_changed(game, match_data)
