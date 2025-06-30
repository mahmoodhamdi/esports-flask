import sqlite3
import logging

logger = logging.getLogger(__name__)

def fetch_teams_from_db(page=1, page_size=10):
    """Fetch teams from database with pagination"""
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        offset = (page - 1) * page_size
        cursor.execute('SELECT team_name, logo_url FROM teams LIMIT ? OFFSET ?', (page_size, offset))
        teams_data = [{'team_name': row[0], 'logo_url': row[1]} for row in cursor.fetchall()]
        cursor.execute('SELECT COUNT(*) FROM teams')
        total_teams = cursor.fetchone()[0]
        conn.close()
        logger.debug(f"Retrieved teams from database, page {page}, size {page_size}")
        return teams_data, total_teams
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching teams: {str(e)}")
        return [], 0

def store_teams_in_db(teams_data):
    """Store teams data in database"""
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM teams')
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