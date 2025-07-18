import re
import os
import shutil
import logging
from datetime import datetime
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
BASE_URL = 'https://liquipedia.net'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}


def convert_timestamp_to_eest(timestamp: int) -> str:
    dt_utc = datetime.utcfromtimestamp(timestamp).replace(tzinfo=ZoneInfo("UTC"))
    dt_eest = dt_utc.astimezone(ZoneInfo("Europe/Athens"))
    return dt_eest.strftime("%B %d, %Y - %H:%M EEST")
def ensure_upload_folder():
    """Create uploads directory if it doesn't exist"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        logger.info(f"Created upload folder: {UPLOAD_FOLDER}")


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file) -> str:
    """Save uploaded file with unique filename, return filename only"""
    if not file or not allowed_file(file.filename):
        return None

    ensure_upload_folder()
    filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

    try:
        file.save(file_path)
        return unique_filename  # فقط اسم الملف
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}")
        return None


def clear_uploads_folder():
    """Clear all files from uploads folder"""
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                logger.debug(f"Deleted file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file {file_path}: {str(e)}")
        logger.info("Cleared uploads folder")


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    if not url:
        return True
    regex = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(regex.match(url))


def is_valid_thumbnail(url: str) -> bool:
    """Validate thumbnail URL (image or link)"""
    if not url:
        return True
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    parsed = urlparse(url)
    return is_valid_url(url) and (
        parsed.path.lower().endswith(image_extensions)
        or parsed.scheme in ('http', 'https'))


def sanitize_input(text: str, max_length: int = None) -> str:
    """Sanitize and trim input text"""
    if not text:
        return ''
    text = text.strip()
    text = re.sub(r'[<>]', '', text)
    if max_length:
        text = text[:max_length]
    return text


def get_html_via_api(game: str, page: str) -> str:
    """Fetch raw HTML of a specific Liquipedia page for a game"""
    try:
        url = f"{BASE_URL}/{game}/{page}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch HTML from {url}: {str(e)}")
        return None


def extract_matches_from_html(html: str) -> dict:
    """Parse group stage matches from Liquipedia HTML"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        boxes = soup.select('div.template-box')
        if not boxes:
            return None

        data = {}
        for group in boxes:
            group_name_tag = group.select_one('.brkts-matchlist-title')
            group_name = group_name_tag.text.strip(
            ) if group_name_tag else 'Unknown Group'
            matches = []

            for match in group.select('.brkts-matchlist-match'):
                teams = match.select('.brkts-matchlist-opponent')
                if len(teams) != 2:
                    continue

                team1 = teams[0].get('aria-label', 'N/A').strip()
                logo1 = BASE_URL + teams[0].select_one(
                    'img')['src'] if teams[0].select_one('img') else 'N/A'
                team2 = teams[1].get('aria-label', 'N/A').strip()
                logo2 = BASE_URL + teams[1].select_one(
                    'img')['src'] if teams[1].select_one('img') else 'N/A'

                match_time_tag = match.select_one('span.timer-object')
                match_time = match_time_tag.text.strip(
                ) if match_time_tag else 'N/A'

                score_tag = match.select_one('.brkts-matchlist-score')
                score = score_tag.text.strip() if score_tag else 'N/A'

                matches.append({
                    "Team1": {
                        "Name": team1,
                        "Logo": logo1
                    },
                    "Team2": {
                        "Name": team2,
                        "Logo": logo2
                    },
                    "MatchTime": match_time,
                    "Score": score
                })

            if matches:
                data[group_name] = matches

        return data if data else None
    except Exception as e:
        logger.error(f"Failed to parse HTML: {str(e)}")
        return None
