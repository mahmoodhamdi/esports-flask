import requests
from bs4 import BeautifulSoup
from app.db import get_connection
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
import random
import logging

logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; rv:125.0) Gecko/20100101 Firefox/125.0'
]

session = requests.Session()
session.headers.update({
    'User-Agent': random.choice(USER_AGENTS),
    'Referer': 'https://www.google.com/',
    'Accept-Language': 'en-US,en;q=0.9',
    'DNT': '1',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'X-Requested-With': 'XMLHttpRequest'
})


def convert_timestamp_to_eest(timestamp: int) -> str:
    dt_utc = datetime.utcfromtimestamp(timestamp).replace(tzinfo=ZoneInfo("UTC"))
    dt_eest = dt_utc.astimezone(ZoneInfo("Europe/Athens"))  # EEST (UTC+3)
    return dt_eest.strftime("%B %d, %Y - %H:%M EEST")


def scrape_matches(game="dota2"):
    """Fetch match data from Liquipedia API and store it in the database."""
    BASE_URL = "https://liquipedia.net"
    API_URL = f"{BASE_URL}/{game}/api.php"
    params = {
        'action': 'parse',
        'page': "Liquipedia:Matches",
        'format': 'json',
        'prop': 'text'
    }

    try:
        response = session.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        html_content = response.json()['parse']['text']['*']
        soup = BeautifulSoup(html_content, "html.parser")
    except requests.RequestException as e:
        logger.error(f"API request failed for {game}: {e}")
        raise

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM game_matches WHERE game = ?', (game,))
        logger.info(f"Cleared existing matches for {game}")

        sections = soup.select('div[data-toggle-area-content]')
        for section in sections:
            section_type = section.get('data-toggle-area-content')
            status = "Upcoming" if section_type == "1" else "Completed" if section_type == "2" else "Other"
            if status == "Other":
                continue

            for match in section.select('.match'):
                team1 = match.select_one('.team-left .team-template-text a')
                team2 = match.select_one('.team-right .team-template-text a')
                logo1 = match.select_one('.team-left img')
                logo2 = match.select_one('.team-right img')
                fmt = match.select_one('.versus-lower abbr')
                score_spans = [s.text.strip() for s in match.select('.versus-upper span') if s.text.strip()]
                score = ":".join(score_spans) if len(score_spans) >= 2 else ""

                timer_span = match.select_one(".timer-object")
                timestamp = timer_span.get("data-timestamp") if timer_span else None
                if timestamp:
                    match_time_str = convert_timestamp_to_eest(int(timestamp))
                    dt = datetime.utcfromtimestamp(int(timestamp)).replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Europe/Athens"))
                    match_date = dt.strftime("%Y-%m-%d")
                else:
                    match_time_str = "N/A"
                    match_date = "N/A"

                stream_div = match.select_one('.match-streams a')
                stream_link = f"{BASE_URL}{stream_div['href']}" if stream_div and stream_div.has_attr('href') else "None"

                tournament_tag = match.select_one('.match-tournament .tournament-name a')
                tournament_icon_tag = match.select_one('.match-tournament .tournament-icon img')

                tournament_name = tournament_tag.text.strip() if tournament_tag else "Unknown"
                tournament_link = f"{BASE_URL}{tournament_tag['href']}" if tournament_tag else None
                tournament_icon_url = f"{BASE_URL}{tournament_icon_tag['src']}" if tournament_icon_tag else None

                team1_logo = f"{BASE_URL}{logo1['src']}" if logo1 else None
                team2_logo = f"{BASE_URL}{logo2['src']}" if logo2 else None

                match_data = (
                    game,
                    status,
                    tournament_name,
                    team1.text.strip() if team1 else "N/A",
                    team2.text.strip() if team2 else "N/A",
                    match_time_str,
                    match_date,
                    score,
                    stream_link,
                    tournament_link,
                    tournament_icon_url,
                    team1_logo,
                    team2_logo,
                    fmt.text.strip() if fmt else "N/A"
                )

                try:
                    cursor.execute('''
                        INSERT INTO game_matches (
                            game, status, tournament_name, team1_name, team2_name, match_time, match_date, score, stream_link,
                            tournament_link, tournament_icon, team1_logo, team2_logo, format
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', match_data)
                    logger.debug(f"Inserted match: {tournament_name} - {match_data[3]} vs {match_data[4]} at {match_time_str}")
                except sqlite3.IntegrityError as e:
                    logger.debug(f"Skipped duplicate match: {tournament_name} - {match_data[3]} vs {match_data[4]} - {e}")

        conn.commit()

        cursor.execute('SELECT DISTINCT match_date FROM game_matches WHERE game = ? ORDER BY match_date', (game,))
        dates = [row[0] for row in cursor.fetchall()]
        logger.info(f"Successfully scraped and stored matches for {game}. Available dates: {dates}")

    except sqlite3.Error as e:
        logger.error(f"Database error during scraping: {e}")
        raise
    finally:
        conn.close()
