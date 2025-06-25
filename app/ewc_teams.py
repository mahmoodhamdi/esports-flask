import sqlite3
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def fetch_ewc_teams(live=False):

    """Fetch Esports World Cup 2025 teams from Liquipedia or database"""

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

    # Fetch from Liquipedia if live=True or no data in database
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    BASE_URL = "https://liquipedia.net"
    url = 'https://liquipedia.net/esports/Esports_World_Cup/2025'

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

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
            logger.error("Could not find the teams table")
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

        # Store in database
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
