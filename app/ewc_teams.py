import sqlite3
from bs4 import BeautifulSoup
import logging
import requests
import json
import hashlib
import os

logger = logging.getLogger(__name__)
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

def fetch_ewc_teams(live=False):
    """Fetch Esports World Cup 2025 teams from Liquipedia or database"""
    params = {
        'action': 'parse',
        'page': PAGE_NAME,
        'format': 'json',
        'prop': 'text'
    }

    if not live:
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()
            cursor.execute('SELECT team_name, logo_url FROM teams')
            teams_data = [{'team_name': row[0], 'logo_url': row[1]} for row in cursor.fetchall()]
            conn.close()
            if teams_data:
                logger.debug("Retrieved teams data from database")
                return teams_data
        except sqlite3.Error as e:
            logger.error(f"Database error while fetching teams: {str(e)}")

    try:
        response = requests.get(API_URL, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return []

        html = response.json().get('parse', {}).get('text', {}).get('*', '')
        current_hash = calculate_hash(html)

        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, 'r', encoding='utf-8') as f:
                old_hash = f.read().strip()
            if current_hash == old_hash:
                print("No changes detected. Skipping update.")
                return []

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
            print("Could not find the teams table.")
            return []

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

        print(f"Teams data updated and saved to {OUTPUT_FILE}")

        # ✅ Store in database
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM teams')  # Clear existing teams
            for team in teams_data:
                cursor.execute('''
                    INSERT INTO teams (team_name, logo_url)
                    VALUES (?, ?)
                ''', (team['team_name'], team['logo_url']))
            conn.commit()
            logger.debug("Stored teams data in database")
        except sqlite3.Error as e:
            logger.error(f"Database error while storing teams: {str(e)}")
        finally:
            conn.close()

        return teams_data

    except requests.RequestException as e:
        logger.error(f"Error fetching teams data: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error processing teams data: {str(e)}")
        return []
