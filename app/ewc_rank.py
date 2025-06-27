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


def get_ewc_rank_data(live=False, week=None, team=None, page=1, per_page=10):
    """
    Get EWC rank data with pagination and filtering support
    
    Args:
        live (bool): If True, fetch from API; if False, use cached data
        week (str): Filter by specific week (e.g., "Week 1")
        team (str): Filter by team name (partial match)
        page (int): Page number for pagination (1-based)
        per_page (int): Number of items per page
    
    Returns:
        dict: Paginated and filtered data with metadata
    """
    if live:
        html = get_html_from_api()
        if html:
            new_data = extract_standings_from_html(html)
            if new_data:
                # Update the JSON file with new data
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
                print("Live data fetched and saved.")
                raw_data = new_data
            else:
                print("Failed to extract live data.")
                raw_data = {}
        else:
            print("Failed to get HTML from API for live data.")
            raw_data = {}
    else:
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            print("Data loaded from file.")
        else:
            print("No cached data found. Fetching live data.")
            return get_ewc_rank_data(live=True, week=week, team=team, page=page, per_page=per_page)
    
    # Apply filters and pagination
    return apply_filters_and_pagination(raw_data, week, team, page, per_page)


def apply_filters_and_pagination(data, week_filter=None, team_filter=None, page=1, per_page=10):
    """
    Apply filters and pagination to the rank data
    
    Args:
        data (dict): Raw data organized by weeks
        week_filter (str): Filter by specific week
        team_filter (str): Filter by team name (case-insensitive partial match)
        page (int): Page number (1-based)
        per_page (int): Items per page
    
    Returns:
        dict: Filtered and paginated data with metadata
    """
    # Flatten data for filtering and pagination
    all_teams = []
    
    for week_name, teams in data.items():
        if week_filter and week_filter.lower() != week_name.lower():
            continue
            
        for team in teams:
            # Add week information to each team record
            team_with_week = team.copy()
            team_with_week['Week'] = week_name
            
            # Apply team filter if specified
            if team_filter:
                if team_filter.lower() not in team['Team'].lower():
                    continue
            
            all_teams.append(team_with_week)
    
    # Sort by ranking within each week, then by week
    def sort_key(team):
        week_num = int(team['Week'].split()[-1]) if team['Week'].split()[-1].isdigit() else 999
        ranking = team['Ranking'].replace('.', '')
        try:
            ranking_num = int(ranking) if ranking.isdigit() else 999
        except:
            ranking_num = 999
        return (week_num, ranking_num)
    
    all_teams.sort(key=sort_key)
    
    # Calculate pagination
    total_items = len(all_teams)
    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division
    
    # Validate page number
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Calculate start and end indices
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Get paginated data
    paginated_teams = all_teams[start_idx:end_idx]
    
    # Prepare response
    result = {
        "data": paginated_teams,
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "next_page": page + 1 if page < total_pages else None,
            "prev_page": page - 1 if page > 1 else None
        },
        "filters": {
            "week": week_filter,
            "team": team_filter
        }
    }
    
    return result


def get_available_weeks():
    """Get list of available weeks"""
    return list(TOGGLE_AREAS.keys())


def get_teams_summary(data):
    """Get summary of teams across all weeks"""
    all_teams = set()
    for week_data in data.values():
        for team in week_data:
            all_teams.add(team['Team'])
    return sorted(list(all_teams))


if __name__ == "__main__":
    # This part will be executed when the script is run directly
    # It will fetch data and save it to the JSON file
    get_ewc_rank_data(live=True)


