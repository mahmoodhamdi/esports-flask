import os
import logging

logger = logging.getLogger(__name__)

# Define the path to the JSON file
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
JSON_FILE_PATH = os.path.join(BASE_DIR, 'app', 'json', 'teams_ewc.json')

# Fallback to root directory if not found
if not os.path.exists(JSON_FILE_PATH):
    JSON_FILE_PATH = os.path.join(BASE_DIR, 'teams_ewc.json')
    logger.warning(f"Fallback JSON path used: {JSON_FILE_PATH}")

logger.info(f"JSON file path resolved to: {JSON_FILE_PATH}")