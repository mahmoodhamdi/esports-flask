import sqlite3
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def get_prize_distribution(live=False):
    """Fetch Esports World Cup 2025 prize distribution from Liquipedia or database"""
    if not live:
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()
            cursor.execute('SELECT place, place_logo, prize, participants, logo_team FROM prize_distribution')
            prize_data = [
                {
                    'place': row[0],
                    'place_logo': row[1],
                    'prize': row[2],
                    'participants': row[3],
                    'logo_team': row[4]
                } for row in cursor.fetchall()
            ]
            conn.close()

            if prize_data:
                logger.debug("Retrieved prize distribution data from database")
                return prize_data
        except sqlite3.Error as e:
            logger.error(f"Database error while fetching prize distribution: {str(e)}")

    # Fetch from Liquipedia if live=True or no data in database
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    BASE_URL = "https://liquipedia.net"
    URL = "https://liquipedia.net/esports/Esports_World_Cup/2025"

    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        prize_table = soup.select_one('div.prizepool-section-tables .csstable-widget')
        prize_data = []

        if not prize_table:
            logger.error("No prize distribution table found on Liquipedia")
            return []

        rows = prize_table.select('div.csstable-widget-row')[1:]  # Skip header
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

        # Store in database
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM prize_distribution')  # Clear existing data
            for prize in prize_data:
                cursor.execute('''
                    INSERT INTO prize_distribution (place, place_logo, prize, participants, logo_team)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    prize['place'],
                    prize['place_logo'],
                    prize['prize'],
                    prize['participants'],
                    prize['logo_team']
                ))
            conn.commit()
            logger.debug("Stored prize distribution data in database")
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
