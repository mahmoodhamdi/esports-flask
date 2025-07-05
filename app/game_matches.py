import requests
from bs4 import BeautifulSoup
from app.db import get_connection
import sqlite3
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

def scrape_matches(game="dota2"):
    """Fetch match data from the API and store it in the database."""
    BASE_URL = "https://liquipedia.net"
    API_URL = f"{BASE_URL}/{game}/api.php"
    params = {
        'action': 'parse',
        'page': "Liquipedia:Matches",
        'format': 'json',
        'prop': 'text'
    }

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        html_content = response.json()['parse']['text']['*']
        soup = BeautifulSoup(html_content, "html.parser")
    except requests.RequestException as e:
        logger.error(f"API request failed for {game}: {e}")
        raise

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for match in soup.select('.match'):
            team1 = match.select_one('.team-left .team-template-text a')
            team2 = match.select_one('.team-right .team-template-text a')
            time_span = match.select_one(".match-bottom-bar .timer-object") or match.select_one(".timer-object-date")
            score_spans = [s.text.strip() for s in match.select('.versus-upper span') if s.text.strip()]
            score = ":::".join(score_spans) if len(score_spans) >= 2 else ""
            tournament_tag = match.select_one('.match-tournament .tournament-name a')
            status = "Upcoming" if match.find_parent('div[data-toggle-area-content="1"]') else "Completed"

            raw_time = time_span.text.strip() if time_span else "N/A"
            formatted_time = raw_time
            if raw_time != "N/A":
                try:
                    dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                    # Convert to CEST for display
                    cest = pytz.timezone("Europe/Paris")
                    dt_cest = dt.astimezone(cest)
                    formatted_time = dt_cest.strftime("%B %d, %Y - %H:%M CEST").replace(" 0", " ")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse match_time '{raw_time}': {e}")

            match_data = (
                game,
                status,
                tournament_tag.text.strip() if tournament_tag else "Unknown",
                team1.text.strip() if team1 else "N/A",
                team2.text.strip() if team2 else "N/A",
                formatted_time,
                score,
                "None",
                None,
                None,
                None,
                None,
                None
            )

            try:
                cursor.execute('''
                    INSERT INTO game_matches (
                        game, status, tournament_name, team1_name, team2_name, match_time, score, stream_link,
                        tournament_link, tournament_icon, team1_logo, team2_logo, format
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', match_data)
                logger.debug(f"Inserted match: {match_data[2]} - {match_data[3]} vs {match_data[4]} at {formatted_time}")
            except sqlite3.IntegrityError:
                logger.debug(f"Skipped duplicate match: {match_data[2]} - {match_data[3]} vs {match_data[4]}")

        conn.commit()
        logger.info(f"Successfully scraped and stored matches for {game}")
    except sqlite3.Error as e:
        logger.error(f"Database error during scraping: {e}")
        raise
    finally:
        conn.close()