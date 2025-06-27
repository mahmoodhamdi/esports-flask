import requests
from bs4 import BeautifulSoup
import json
import hashlib
import os

API_URL = 'https://liquipedia.net/esports/api.php'
BASE_URL = 'https://liquipedia.net'
OUTPUT_FILE = "club_championship_standings_api.json"

TOGGLE_AREAS = {
    "Week 1": "4",
    "Week 2": "8",
    "Week 3": "11",
    "Week 4": "15",
    "Week 5": "18",
    "Week 6": "22",
    "Week 7": "25"
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}


def get_html_from_api():
    params = {
        'action': 'parse',
        'page': 'Esports_World_Cup/2025/Club_Championship_Standings',
        'format': 'json',
        'prop': 'text'
    }
    response = requests.get(API_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'parse' in data and 'text' in data['parse'] and '*' in data['parse']['text']:
            return data['parse']['text']['*']
    print("Failed to get HTML from API")
    return None


def find_main_table(soup):
    tables = soup.find_all('table', class_='wikitable')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            if row.get("data-toggle-area-content"):
                return table
    return None


def calculate_hash(week_name, team_name, points):
    raw_string = f"{week_name}-{team_name}-{points}"
    return hashlib.md5(raw_string.encode('utf-8')).hexdigest()


def extract_standings_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = find_main_table(soup)
    if not table:
        print("Could not find main table.")
        return {}

    standings_by_week = {week: [] for week in TOGGLE_AREAS.keys()}
    rows = table.find_all('tr')

    for row in rows[1:]:
        area = row.get("data-toggle-area-content")
        if not area:
            continue

        week_name = next((week for week, val in TOGGLE_AREAS.items() if val == area), None)
        if not week_name:
            continue

        cols = row.find_all('td')
        if len(cols) < 5:
            continue

        team_name_tag = row.select_one('span.team-template-text')
        team_name = team_name_tag.get_text(strip=True) if team_name_tag else "Unknown"

        light_img = row.select_one('span.team-template-lightmode img')
        dark_img = row.select_one('span.team-template-darkmode img')

        light_logo = BASE_URL + light_img['src'] if light_img else None
        dark_logo = BASE_URL + dark_img['src'] if dark_img else None

        points = cols[3].get_text(strip=True)

        team_data = {
            "id": calculate_hash(week_name, team_name, points),
            "Ranking": cols[0].get_text(strip=True),
            "Trend": cols[1].get_text(strip=True),
            "Team": team_name,
            "Logo_Light": light_logo,
            "Logo_Dark": dark_logo,
            "Points": points,
            "Total Rank": cols[4].get_text(strip=True)
        }

        standings_by_week[week_name].append(team_data)

    return standings_by_week


def flatten_hashes(data):
    return set(item["id"] for week_data in data.values() for item in week_data)


def update_existing_data(old_data, new_data):
    updated_data = {}
    for week, new_teams in new_data.items():
        old_teams = {item["id"]: item for item in old_data.get(week, [])}
        updated_week = []

        for team in new_teams:
            old_team = old_teams.get(team["id"])
            if not old_team or team != old_team:
                updated_week.append(team)
            else:
                updated_week.append(old_team)

        updated_data[week] = updated_week
    return updated_data


def get_ewc_rank_data(live=False):
    if live:
        html = get_html_from_api()
        if html:
            new_data = extract_standings_from_html(html)
            if new_data:
                # Update the JSON file with new data
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
                print("Live data fetched and saved.")
                return new_data
            else:
                print("Failed to extract live data.")
                return {}
        else:
            print("Failed to get HTML from API for live data.")
            return {}
    else:
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("Data loaded from file.")
            return data
        else:
            print("No cached data found. Fetching live data.")
            return get_ewc_rank_data(live=True)


if __name__ == "__main__":
    # This part will be executed when the script is run directly
    # It will fetch data and save it to the JSON file
    get_ewc_rank_data(live=True)


