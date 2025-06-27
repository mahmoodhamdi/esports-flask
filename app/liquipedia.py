import json
import requests
from bs4 import BeautifulSoup
import hashlib
import os

BASE_URL = 'https://liquipedia.net'
GAME_PAGE = 'Esports_World_Cup/2025'
API_URL = f'{BASE_URL}/esports/api.php'
HASH_FILE = 'ewc_2025_games_hash.txt'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def calculate_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def fetch_ewc_games_from_web():
    params = {
        'action': 'parse',
        'page': GAME_PAGE,
        'format': 'json',
        'prop': 'text'
    }

    try:
        response = requests.get(API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
    except Exception as e:
        print(f"API request failed: {e}")
        return []

    html = response.json().get('parse', {}).get('text', {}).get('*', '')
    current_hash = calculate_hash(html)

    # check if content changed
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r', encoding='utf-8') as f:
            if f.read().strip() == current_hash:
                print("No changes detected.")
                return []

    soup = BeautifulSoup(html, 'html.parser')
    games_data = []

    target_table = next(
        (th.find_parent('table') for th in soup.select('th[colspan="8"]') if 'List of Tournaments' in th.text),
        None
    )

    if not target_table:
        print("Target table not found.")
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

    # Save the new hash
    with open(HASH_FILE, 'w', encoding='utf-8') as f:
        f.write(current_hash)

    return games_data
