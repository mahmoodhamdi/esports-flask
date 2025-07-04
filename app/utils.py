import re
import os
import shutil
import logging
from datetime import datetime
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
BASE_URL = 'https://liquipedia.net'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'image/*'
}

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
            group_name = group_name_tag.text.strip() if group_name_tag else 'Unknown Group'
            matches = []

            for match in group.select('.brkts-matchlist-match'):
                teams = match.select('.brkts-matchlist-opponent')
                if len(teams) != 2:
                    continue

                team1 = teams[0].get('aria-label', 'N/A').strip()
                logo1 = BASE_URL + teams[0].select_one('img')['src'] if teams[0].select_one('img') else ''
                team2 = teams[1].get('aria-label', 'N/A').strip()
                logo2 = BASE_URL + teams[1].select_one('img')['src'] if teams[1].select_one('img') else ''

                match_time_tag = match.select_one('span.timer-object')
                match_time = match_time_tag.text.strip() if match_time_tag else ''

                score_tag = match.select_one('.brkts-matchlist-score')
                score = score_tag.text.strip() if score_tag else ''

                matches.append({
                    "Team1": {"Name": team1, "Logo": logo1},
                    "Team2": {"Name": team2, "Logo": logo2},
                    "MatchTime": match_time,
                    "Score": score
                })

            if matches:
                data[group_name] = matches

        return data if data else None
    except Exception as e:
        logger.error(f"Failed to parse HTML: {str(e)}")
        return None

def ensure_upload_folder():
    """Create uploads directory if it doesn't exist"""
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        logger.debug(f"Ensured upload folder exists: {UPLOAD_FOLDER}")
    except OSError as e:
        logger.error(f"Failed to create upload folder: {str(e)}")
        raise

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file) -> str:
    """Save uploaded file with unique filename and validation"""
    if not file or not allowed_file(file.filename):
        logger.debug(f"Invalid file: {file.filename if file else 'None'}")
        return None

    try:
        ensure_upload_folder()
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        if file_size > 5 * 1024 * 1024:  # 5MB limit
            os.remove(file_path)
            logger.warning(f"File too large: {file_size} bytes")
            raise ValueError("File too large, maximum 5MB")

        logger.debug(f"Saved file: {file_path}")
        return f"/{UPLOAD_FOLDER}/{unique_filename}"
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}")
        raise RuntimeError(f"Failed to save file: {str(e)}")

def clear_uploads_folder():
    """Clear all files from uploads folder"""
    try:
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        logger.debug(f"Deleted file: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        logger.debug(f"Deleted directory: {file_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete {file_path}: {str(e)}")
            logger.info("Cleared uploads folder")
    except Exception as e:
        logger.error(f"Failed to clear uploads folder: {str(e)}")
        raise

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
    """Validate thumbnail URL"""
    if not url:
        return True
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    parsed = urlparse(url)
    if not is_valid_url(url):
        return False
    
    try:
        response = requests.head(url, headers=HEADERS, timeout=5)
        if response.status_code != 200:
            return False
        content_type = response.headers.get('content-type', '').lower()
        return content_type.startswith('image/') or parsed.path.lower().endswith(image_extensions)
    except requests.RequestException:
        logger.warning(f"Failed to validate thumbnail URL: {url}")
        return False

def is_valid_date(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def sanitize_input(text: str, max_length: int = None) -> str:
    """Sanitize input text with stricter rules"""
    if not text:
        return ''
    # Remove HTML tags and dangerous characters
    text = re.sub(r'[<>%`]', '', text.strip())
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    if max_length:
        text = text[:max_length]
    return text