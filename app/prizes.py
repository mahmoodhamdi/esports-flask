import sqlite3
import requests
from bs4 import BeautifulSoup
import logging
import hashlib

logger = logging.getLogger(__name__)

def get_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

def get_prize_distribution(live=False, url=None):
    """Fetch prize distribution for a specific tournament"""
    BASE_URL = "https://liquipedia.net"
    URL = url or f"{BASE_URL}/esports/Esports_World_Cup/2025"
    url_hash = get_url_hash(URL)

    if not live:
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT place, place_logo, prize, participants, logo_team 
                FROM prize_distribution 
                WHERE url_hash = ?
            ''', (url_hash,))
            rows = cursor.fetchall()
            conn.close()

            if rows:
                logger.debug("Retrieved prize distribution data from DB")
                return [
                    {
                        'place': row[0],
                        'place_logo': row[1],
                        'prize': row[2],
                        'participants': row[3],
                        'logo_team': row[4]
                    } for row in rows
                ]
        except sqlite3.Error as e:
            logger.error(f"Database error while fetching prize distribution: {str(e)}")

    # Fetch from web if no data or live=True
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        prize_table = soup.select_one('div.prizepool-section-tables .csstable-widget')
        prize_data = []

        if not prize_table:
            logger.error("No prize distribution table found")
            return []

        rows = prize_table.select('div.csstable-widget-row')[1:]
        for row in rows:
            cell = row.select('div.csstable-widget-cell')
            if len(cell) >= 3:
                place_cell = cell[0]
                place = place_cell.get_text(strip=True)
                place_img = place_cell.select_one('img')
                place_logo = BASE_URL + place_img['src'] if place_img else None

                prize = cell[1].get_text(strip=True)

                participant_cell = cell[2]
                participants = participant_cell.get_text(strip=True)
                logo_tag = participant_cell.select_one('.team-template-lightmode img')
                logo_team = BASE_URL + logo_tag['src'] if logo_tag else None

                prize_data.append({
                    'place': place,
                    'place_logo': place_logo,
                    'prize': prize,
                    'participants': participants,
                    'logo_team': logo_team
                })

        # Store in DB with url_hash
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()

            # Ensure column url_hash exists (run only once safely)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prize_distribution (
                    place TEXT,
                    place_logo TEXT,
                    prize TEXT,
                    participants TEXT,
                    logo_team TEXT,
                    url_hash TEXT
                )
            ''')

            cursor.execute('DELETE FROM prize_distribution WHERE url_hash = ?', (url_hash,))
            for item in prize_data:
                cursor.execute('''
                    INSERT INTO prize_distribution 
                    (place, place_logo, prize, participants, logo_team, url_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    item['place'],
                    item['place_logo'],
                    item['prize'],
                    item['participants'],
                    item['logo_team'],
                    url_hash
                ))
            conn.commit()
            logger.debug("Stored prize distribution in DB")

        except sqlite3.Error as e:
            logger.error(f"Database error while storing prize distribution: {str(e)}")
        finally:
            conn.close()

        return prize_data

    except requests.RequestException as e:
        logger.error(f"Error fetching prize distribution from Liquipedia: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error processing prize distribution: {str(e)}")
        return []
