import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

BASE_URL = 'https://liquipedia.net'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def get_player_transfer(game_name):
    url = f"{BASE_URL}/{game_name}/Portal:Transfers"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        table_transfers = soup.select_one('div.divTable.mainpage-transfer.Ref')
        if not table_transfers:
            logger.error(f"No transfer table found for {game_name}")
            return []

        data = []
        rows = table_transfers.select('div.divRow')
        for row in rows:
            try:
                date_cell = row.select_one('div.Date')
                date = date_cell.text.strip() if date_cell else 'N/A'

                players = []
                player_blocks = row.select('div.Name .block-player')
                for block in player_blocks:
                    name_tag = block.select_one('.name a')
                    name = name_tag.text.strip() if name_tag else "N/A"
                    flag_img = block.select_one('img')
                    flag_logo = BASE_URL + flag_img['src'] if flag_img else None
                    players.append({"Name": name, "Flag": flag_logo})

                old_light = row.select_one('div.OldTeam .team-template-lightmode img')
                old_dark = row.select_one('div.OldTeam .team-template-darkmode img')
                old_name = old_light['alt'] if old_light else (old_dark['alt'] if old_dark else "None")
                old_logo_light = BASE_URL + old_light['src'] if old_light else None
                old_logo_dark = BASE_URL + old_dark['src'] if old_dark else None

                new_light = row.select_one('div.NewTeam .team-template-lightmode img')
                new_dark = row.select_one('div.NewTeam .team-template-darkmode img')
                new_name = new_light['alt'] if new_light else (new_dark['alt'] if new_dark else "None")
                new_logo_light = BASE_URL + new_light['src'] if new_light else None
                new_logo_dark = BASE_URL + new_dark['src'] if new_dark else None

                for player in players:
                    unique_id = f"{date}_{player['Name']}"

                    data.append({
                        "Unique_ID": unique_id,
                        "Game": game_name,
                        "Date": date,
                        "PlayerName": player['Name'],
                        "PlayerFlag": player['Flag'],
                        "OldTeamName": old_name,
                        "OldTeamLogoLight": old_logo_light,
                        "OldTeamLogoDark": old_logo_dark,
                        "NewTeamName": new_name,
                        "NewTeamLogoLight": new_logo_light,
                        "NewTeamLogoDark": new_logo_dark
                    })

            except Exception as e:
                logger.error(f"Failed to parse a transfer row: {e}")
                continue

        return data
    except Exception as e:
        logger.error(f"Error fetching player transfers for {game_name}: {e}")
        return []


def store_transfers_in_db(game_name):
    try:
        transfers = get_player_transfer(game_name)
        if not transfers:
            return False, f"No transfers found for game '{game_name}'"

        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()

        # Insert or ignore duplicates by unique_id
        for t in transfers:
            cursor.execute('''
                INSERT OR IGNORE INTO transfers (
                    unique_id, game, date, player_name, player_flag,
                    old_team_name, old_team_logo_light, old_team_logo_dark,
                    new_team_name, new_team_logo_light, new_team_logo_dark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                t['Unique_ID'], t['Game'], t['Date'], t['PlayerName'], t['PlayerFlag'],
                t['OldTeamName'], t['OldTeamLogoLight'], t['OldTeamLogoDark'],
                t['NewTeamName'], t['NewTeamLogoLight'], t['NewTeamLogoDark']
            ))

        conn.commit()
        conn.close()

        return True, f"{len(transfers)} transfers stored for game '{game_name}'"
    except Exception as e:
        logger.error(f"Error storing transfers in DB: {e}")
        return False, str(e)

def get_transfers_from_db(game_name=None, page=1, per_page=50, sort_by='date', sort_order='desc'):
    valid_sort_columns = {'date', 'player_name', 'game', 'old_team_name', 'new_team_name'}
    if sort_by not in valid_sort_columns:
        sort_by = 'date'
    sort_order = sort_order.lower()
    if sort_order not in {'asc', 'desc'}:
        sort_order = 'desc'

    offset = (page - 1) * per_page

    try:
        conn = sqlite3.connect('news.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        base_query = "SELECT * FROM transfers"
        params = []
        if game_name:
            base_query += " WHERE game = ?"
            params.append(game_name)

        base_query += f" ORDER BY {sort_by} {sort_order.upper()}"
        base_query += " LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        cursor.execute(base_query, params)
        rows = cursor.fetchall()

        # Also get total count for pagination info
        count_query = "SELECT COUNT(*) FROM transfers"
        count_params = []
        if game_name:
            count_query += " WHERE game = ?"
            count_params.append(game_name)

        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]

        conn.close()

        return {
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "data": [dict(row) for row in rows]
        }

    except Exception as e:
        logger.error(f"Error fetching transfers from DB: {e}")
        return {
            "total": 0,
            "page": page,
            "per_page": per_page,
            "data": []
        }
