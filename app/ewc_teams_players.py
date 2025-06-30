import requests
from bs4 import BeautifulSoup
import json
import hashlib
import random
from app.crud.ewc_teams_players_crud import (
    insert_ewc_team_player_data,
    get_ewc_team_player_data,
    update_ewc_team_player_data,
    get_all_ewc_team_player_data
)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/125.0.0.0 Safari/537.36'
]

HEADERS = {
    'User-Agent': random.choice(USER_AGENTS),
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/'
}

BASE_URL = 'https://liquipedia.net'
API_URL_TEMPLATE = 'https://liquipedia.net/{game}/api.php'


def fetch_html_via_api(game, page_title):
    """Fetch HTML content via Liquipedia API"""
    api_url = API_URL_TEMPLATE.format(game=game)
    params = {
        'action': 'parse',
        'page': page_title,
        'format': 'json',
        'prop': 'text'
    }
    try:
        res = requests.get(api_url, headers=HEADERS, params=params)
        res.raise_for_status()
        data = res.json()
        html = data['parse']['text']['*']
        return BeautifulSoup(html, 'html.parser')
    except Exception as e:
        print(f"Error fetching API HTML for {page_title}: {e}")
        return None


def compute_hash(data_dict):
    """Compute MD5 hash of data dictionary"""
    json_str = json.dumps(data_dict, sort_keys=True)
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()


def scrape_tournament_teams_players(game, page_title):
    """Scrape tournament teams and players data from Liquipedia"""
    print(f"Loading tournament: {page_title} ({game})")
    main_soup = fetch_html_via_api(game, page_title)
    if not main_soup:
        raise Exception("Failed to load tournament page via API.")

    teams_data = []
    team_cards = main_soup.select('div.teamcard')

    for card in team_cards:
        team_name_tag = card.select_one('center a')
        team_name = team_name_tag.text.strip() if team_name_tag else 'Unknown Team'
        toggle_area = card.get('data-toggle-area')

        team_info = {
            'Team': team_name
        }

        # Extract placement and tournament info
        placement_td = card.select_one('td.teamcard-placement')
        if placement_td:
            placement = placement_td.select_one('b.placement-text')
            tournament_tag = placement_td.select_one('a[title]')
            tournament_name = tournament_tag['title'] if tournament_tag else None
            tournament_logo = BASE_URL + tournament_tag.select_one('img')['src'] if tournament_tag and tournament_tag.select_one('img') else None
            years_tag = placement_td.select_one('b > b')
            years = years_tag.get_text(strip=True) if years_tag else None

            team_info.update({
                'Placement': placement.get_text(" ", strip=True) if placement else None,
                'Tournament': tournament_name,
                'Tournament_Logo': tournament_logo,
                'Years': years
            })

        # Extract players data
        table = card.find_next(lambda tag: tag.name == "table" and tag.get("data-toggle-area-content") == toggle_area)
        players = []

        if table:
            for row in table.select('tr'):
                th = row.select_one('th')
                td = row.select_one('td')
                if th and td:
                    role = th.text.strip()
                    country_tag = td.select_one('span.flag a')
                    country = country_tag['title'] if country_tag else 'Unknown Country'
                    country_logo = BASE_URL + country_tag.select_one('img')['src'] if country_tag and country_tag.select_one('img') else None
                    links = td.select('a[title]')
                    player_tag = links[1] if len(links) > 1 else None
                    player_name = player_tag.get_text(strip=True) if player_tag else 'Unknown Player'
                    won_before = bool(row.select_one('i.fa-trophy-alt'))

                    player_data = {
                        'Role': role,
                        'Country': country,
                        'country_logo': country_logo,
                        'Player': player_name,
                        'HasWonBefore': won_before
                    }
                    players.append(player_data)

        if players:
            team_info['Players'] = players
            teams_data.append(team_info)

    return teams_data


def apply_filters(data, team_name_filter, player_name_filter, country_filter, has_won_before_filter, search_query):
    filtered_data = []
    for team_info in data:
        team_name = team_info.get('Team', '').lower()
        players = team_info.get('Players', [])

        team_match = True
        if team_name_filter:
            team_match = team_name_filter.lower() in team_name

        player_match = False
        country_match = False
        won_before_match = False
        general_search_match = False

        if players:
            for player_data in players:
                player_name = player_data.get('Player', '').lower()
                country = player_data.get('Country', '').lower()
                has_won_before = player_data.get('HasWonBefore', False)

                if player_name_filter and player_name_filter.lower() in player_name:
                    player_match = True
                if country_filter and country_filter.lower() in country:
                    country_match = True
                if has_won_before_filter is not None and has_won_before == has_won_before_filter:
                    won_before_match = True

                if search_query:
                    search_query_lower = search_query.lower()
                    if search_query_lower in team_name or \
                       search_query_lower in player_name or \
                       search_query_lower in country or \
                       search_query_lower in team_info.get('Tournament', '').lower():
                        general_search_match = True

        if team_match and \
           (not player_name_filter or player_match) and \
           (not country_filter or country_match) and \
           (has_won_before_filter is None or won_before_match) and \
           (not search_query or general_search_match):
            filtered_data.append(team_info)

    return filtered_data


def fetch_ewc_teams_players(game="valorant", page_title="Esports_World_Cup/2025", live=False, team_name_filter=None, player_name_filter=None, country_filter=None, has_won_before_filter=None, search_query=None):
    """
    Fetch EWC teams and players data either from cache or live API, with filtering capabilities.
    
    Args:
        game (str): Game name (default: valorant)
        page_title (str): Liquipedia page title (default: Esports_World_Cup/2025)
        live (bool): If True, fetch from API; if False, fetch from database
        team_name_filter (str): Filter by team name (partial match, case-insensitive)
        player_name_filter (str): Filter by player name (partial match, case-insensitive)
        country_filter (str): Filter by player country (partial match, case-insensitive)
        has_won_before_filter (bool): Filter by whether player has won before
        search_query (str): General search query across team name, player name, country, and tournament
    
    Returns:
        list: Teams and players data
    """
    teams_data = []
    if live:
        # Fetch live data from API
        try:
            teams_data = scrape_tournament_teams_players(game, page_title)
            
            # Store/update in database
            for team in teams_data:
                team_name = team.get('Team')
                placement = team.get('Placement')
                tournament = team.get('Tournament')
                tournament_logo = team.get('Tournament_Logo')
                years = team.get('Years')
                players = team.get('Players', [])
                
                # Compute hash for change detection
                team_hash = compute_hash(team)
                
                # Check if team exists in database
                existing_team = get_ewc_team_player_data(game, team_name)
                
                if existing_team:
                    # Update existing team if hash is different
                    if existing_team.get('hash_value') != team_hash:
                        update_ewc_team_player_data(
                            game, team_name, placement, tournament, 
                            tournament_logo, years, players, team_hash
                        )
                else:
                    # Insert new team
                    insert_ewc_team_player_data(
                        game, team_name, placement, tournament, 
                        tournament_logo, years, players, team_hash
                    )
            
        except Exception as e:
            print(f"Error fetching live data: {e}")
            # Fallback to database if API fails
            teams_data = get_all_ewc_team_player_data(game) or []
    else:
        # Fetch from database
        cached_data = get_all_ewc_team_player_data(game)
        if cached_data:
            # Transform database format to API format
            for team in cached_data:
                team_info = {
                    'Team': team['team_name'],
                    'Placement': team['placement'],
                    'Tournament': team['tournament'],
                    'Tournament_Logo': team['tournament_logo'],
                    'Years': team['years'],
                    'Players': team['players']
                }
                teams_data.append(team_info)
        else:
            # No cached data, fetch live as fallback
            teams_data = fetch_ewc_teams_players(game, page_title, live=True, team_name_filter=team_name_filter, player_name_filter=player_name_filter, country_filter=country_filter, has_won_before_filter=has_won_before_filter, search_query=search_query)

    # Apply filters to the fetched data
    return apply_filters(teams_data, team_name_filter, player_name_filter, country_filter, has_won_before_filter, search_query)


