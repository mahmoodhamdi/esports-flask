import sqlite3
import requests
import json
import logging
import hashlib
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def get_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

def get_ewc_information(live=False, url="https://liquipedia.net/esports/Esports_World_Cup/2025"):
    """Fetch tournament information from Liquipedia or database"""
    url_hash = get_url_hash(url)

    if not live:
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ewc_info WHERE url_hash = ? ORDER BY updated_at DESC LIMIT 1', (url_hash,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'header': row[1],
                    'series': row[2],
                    'organizers': row[3],
                    'location': row[4],
                    'prize_pool': row[5],
                    'start_date': row[6],
                    'end_date': row[7],
                    'liquipedia_tier': row[8],
                    'logo_light': row[9],
                    'logo_dark': row[10],
                    'location_logo': row[11],
                    'social_links': json.loads(row[12]) if row[12] else [],
                    'updated_at': row[13]
                }
        except sqlite3.Error as e:
            logger.error(f"DB error while fetching info: {str(e)}")

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        box = soup.select_one('div.fo-nttax-infobox')
        if not box:
            logger.error("No info box found.")
            return {}

        data = {}
        data['header'] = box.select_one('div.infobox-header.wiki-backgroundcolor-light').text.strip()

        for item in box.select('div.infobox-cell-2.infobox-description'):
            key = item.text.strip().rstrip(":")
            val = item.find_next_sibling()
            if val:
                data[key.lower().replace(" ", "_")] = val.text.strip()

        data['logo_light'] = "https://liquipedia.net" + box.select_one('.infobox-image.lightmode img')['src']
        data['logo_dark'] = "https://liquipedia.net" + box.select_one('.infobox-image.darkmode img')['src']

        loc_img = box.select_one('div.infobox-cell-2.infobox-description:contains("Location") + div span.flag img')
        data['location_logo'] = "https://liquipedia.net" + loc_img['src'] if loc_img else None

        links = []
        for a in box.select('div.infobox-center.infobox-icons a.external.text'):
            href = a.get('href')
            icon = a.select_one('i')
            if icon and href:
                platform = icon['class'][-1].replace('lp-', '')
                links.append({'platform': platform, 'link': href})
        data['social_links'] = links

        # Save to DB
        try:
            conn = sqlite3.connect('news.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM ewc_info WHERE url_hash = ?', (url_hash,))
            cursor.execute('''
                INSERT INTO ewc_info (
                    header, series, organizers, location, prize_pool, 
                    start_date, end_date, liquipedia_tier, logo_light, 
                    logo_dark, location_logo, social_links, url_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('header'), data.get('series'), data.get('organizers'), data.get('location'),
                data.get('prize_pool'), data.get('start_date'), data.get('end_date'), data.get('liquipedia_tier'),
                data.get('logo_light'), data.get('logo_dark'), data.get('location_logo'),
                json.dumps(data.get('social_links')), url_hash
            ))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"DB error while storing info: {str(e)}")
        finally:
            conn.close()

        return data

    except Exception as e:
        logger.error(f"Error fetching or processing info: {str(e)}")
        return {}
