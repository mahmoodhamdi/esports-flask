# app/ewc_events.py
import sqlite3
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def get_ewc_events(live=False):
    """Fetch Esports World Cup 2025 events from Liquipedia or database"""
    if not live:
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name, link FROM events')
            events_data = [{'name': row[0], 'link': row[1]} for row in cursor.fetchall()]
            conn.close()
            
            if events_data:
                logger.debug("Retrieved events data from database")
                return events_data
        except sqlite3.Error as e:
            logger.error(f"Database error while fetching events: {str(e)}")
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    BASE_URL = "https://liquipedia.net"
    url = 'https://liquipedia.net/esports/Esports_World_Cup/2025'
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        events_data = []
        events_headers = soup.select_one('div.esports-team-game-list')

        if not events_headers:
            logger.error("Could not find the events section")
            return []
        
        for span in events_headers.select('span > a'):
            name = span.text.strip()
            link = span['href'].strip()
            full_link = link if link.startswith('http') else BASE_URL + link

            events_data.append({
                "name": name,
                "link": full_link
            })
        
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM events')
            for event in events_data:
                cursor.execute('''
                    INSERT INTO events (name, link)
                    VALUES (?, ?)
                ''', (event['name'], event['link']))
            conn.commit()
            logger.debug("Stored events data in database")
        except sqlite3.Error as e:
            logger.error(f"Database error while storing events: {str(e)}")
        finally:
            conn.close()

        return events_data
    
    except requests.RequestException as e:
        logger.error(f"Error fetching events data: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error processing events data: {str(e)}")
        return []
