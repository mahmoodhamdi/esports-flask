from bs4 import BeautifulSoup
import requests
import json
import hashlib
import os
from app.crud.ewc_teams import store_teams_in_db

BASE_URL = "https://liquipedia.net"
API_URL = f"{BASE_URL}/esports/api.php"
PAGE_NAME = "Esports_World_Cup/2025"
HASH_FILE = "teams_ewc_hash.txt"
OUTPUT_FILE = "teams_ewc.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def calculate_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def fetch_ewc_teams(live=False, page=1, page_size=10):
    """Fetch Esports World Cup 2025 teams from Liquipedia or database with pagination"""
    if not live:
        from app.crud.ewc_teams import fetch_teams_from_db
        return fetch_teams_from_db(page, page_size)

    try:
        params = {
            'action': 'parse',
            'page': PAGE_NAME,
            'format': 'json',
            'prop': 'text'
        }
        response = requests.get(API_URL, headers=HEADERS, params=params)
        if response.status_code != 200:
            return [], 0

        html = response.json().get('parse', {}).get('text', {}).get('*', '')
        current_hash = calculate_hash(html)

        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, 'r', encoding='utf-8') as f:
                old_hash = f.read().strip()
            if current_hash == old_hash:
                return [], 0

        soup = BeautifulSoup(html, 'html.parser')
        teams_data = []

        all_tables = soup.select('div.table-responsive table.wikitable.sortable')
        target_table = None
        for table in all_tables:
            headers_row = table.select_one('tr')
            headers_ths = headers_row.select('th') if headers_row else []
            if headers_ths and 'Team Name' in headers_ths[0].text:
                target_table = table
                break

        if not target_table:
            return [], 0

        rows = target_table.select('tr')[1:]
        for row in rows:
            cols = row.select('td')
            if len(cols) >= 1:
                team_name = cols[0].text.strip()
                logo_tag = cols[0].select_one('img')
                logo_url = BASE_URL + logo_tag['src'] if logo_tag else None
                teams_data.append({
                    'team_name': team_name,
                    'logo_url': logo_url
                })

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(teams_data, f, ensure_ascii=False, indent=2)

        with open(HASH_FILE, 'w', encoding='utf-8') as f:
            f.write(current_hash)

        store_teams_in_db(teams_data)

        total_teams = len(teams_data)
        start = (page - 1) * page_size
        end = start + page_size
        return teams_data[start:end], total_teams

    except requests.RequestException:
        return [], 0