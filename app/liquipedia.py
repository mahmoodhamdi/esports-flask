import requests
from bs4 import BeautifulSoup

def fetch_ewc_games_from_web():
    BASE_URL = "https://liquipedia.net"
    url = f"{BASE_URL}/esports/Esports_World_Cup/2025"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        games_data = []

        target_table = None
        for th in soup.select('th[colspan="8"]'):
            if 'List of Tournaments' in th.text:
                target_table = th.find_parent('table')
                break

        if not target_table:
            return []

        for row in target_table.select('tr')[1:]:
            cols = row.select('td')
            if len(cols) >= 4:
                game_name = cols[0].text.strip()
                if not game_name:
                    continue
                logo = cols[0].select_one('img')
                logo_url = BASE_URL + logo['src'] if logo else None
                games_data.append({"game_name": game_name, "logo_url": logo_url})

        return games_data

    except Exception as e:
        print(f"Error fetching from Liquipedia: {e}")
        return []
