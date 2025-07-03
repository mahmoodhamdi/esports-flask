import requests
from bs4 import BeautifulSoup
import json
import random

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

def fetch_teams_players(game: str, tournament: str) -> list[dict]:
    main_soup = fetch_html_via_api(game, tournament)
    if not main_soup:
        raise Exception(f"Failed to load tournament page {tournament} for game {game} via API.")

    teams_data = []
    team_cards = main_soup.select('div.teamcard')

    for card in team_cards:
        team_name_tag = card.select_one('center a')
        team_name = team_name_tag.text.strip() if team_name_tag else 'Unknown Team'
        toggle_area = card.get('data-toggle-area')

        team_info = {'Team': team_name}

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
                    player_link = BASE_URL + player_tag['href'] if player_tag else None
                    won_before = bool(row.select_one('i.fa-trophy-alt'))

                    players.append({
                        'Role': role,
                        'Country': country,
                        'country_logo': country_logo,
                        'Player': player_name,
                        'player_link': player_link,
                        'HasWonBefore': won_before
                    })

        if players:
            team_info['Players'] = players
            teams_data.append(team_info)

    return teams_data