import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import random
import time

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

BASE_URL = "https://liquipedia.net"

def get_html_from_api(game: str, page: str) -> str | None:
    """Fetch HTML content from Liquipedia API for a given game and page."""
    api_url = f"{BASE_URL}/{game}/api.php"
    params = {
        'action': 'parse',
        'page': page,
        'format': 'json',
        'prop': 'text'
    }
    try:
        time.sleep(random.uniform(1, 3))
        response = session.get(api_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['parse']['text']['*']
        else:
            print(f"HTTP {response.status_code}: Failed to fetch {page} for {game}")
            return None
    except Exception as e:
        print(f"Exception during request: {e}")
        return None

def get_player_info(game: str, player_page_name: str) -> tuple[dict, str]:
    """Fetch player information from Liquipedia API."""
    html = get_html_from_api(game, player_page_name)
    if not html:
        return {}, player_page_name

    soup = BeautifulSoup(html, 'html.parser')
    data_card = {}

    info_box = soup.select_one('div.fo-nttax-infobox')
    if not info_box:
        print("Could not find player info box on the page.")
        return {}, player_page_name

    header = info_box.select_one('div.infobox-header')
    if header:
        data_card['Name'] = header.get_text(strip=True)

    team_logo_imgs = info_box.select('div.infobox-header span.team-template-team-icon')
    team_logos, team_names = {}, {}
    added_links, team_count = set(), 1

    for team_icon in team_logo_imgs:
        logo_img = team_icon.select_one('img')
        team_link = team_icon.select_one('a')
        if logo_img and logo_img.get('src'):
            logo_url = BASE_URL + logo_img['src']
            if logo_url not in added_links:
                team_logos[f"team{team_count}_logo"] = logo_url
                team_names[f"team{team_count}"] = team_link['title'] if team_link and team_link.get('title') else "Unknown"
                added_links.add(logo_url)
                team_count += 1
        if team_count > 2:
            break

    if team_logos:
        data_card["Team_Logos"] = team_logos
    if team_names:
        data_card["Teams"] = team_names

    player_img = info_box.select_one('div.infobox-image-wrapper img')
    if player_img and player_img.get('src'):
        data_card['Player_Image'] = BASE_URL + player_img['src']

    desired_fields = {
        'Romanized Name', 'Nationality', 'Born', 'Region', 'Years Active (Player)',
        'Role', 'Alternate IDs', 'Approx. Total Winnings', 'Signature Hero'
    }

    rows = info_box.select('div.infobox-cell-2.infobox-description')
    player_info = {}
    for desc in rows:
        key = desc.text.strip().rstrip(':')
        value_div = desc.find_next_sibling()
        if not value_div or key not in desired_fields:
            continue

        if key == "Signature Hero":
            heroes, hero_imgs = [], []
            links = value_div.select('a')
            for link in links:
                name = link.get('title') or link.text.strip()
                img = link.select_one('img')
                if name:
                    heroes.append(name)
                if img and img.get('src'):
                    hero_imgs.append(BASE_URL + img['src'])
            player_info["Signature_Hero"] = {
                "names": heroes,
                "images": hero_imgs
            }
        else:
            text_value = value_div.get_text(strip=True)
            img_tag = value_div.select_one('img')
            if img_tag and img_tag.get('src'):
                player_info[key] = {
                    "text": text_value,
                    "image": BASE_URL + img_tag['src']
                }
            else:
                player_info[key] = text_value

    if player_info:
        data_card["Player_Information"] = player_info

    social_links = []
    links = info_box.select('div.infobox-center.infobox-icons a.external.text')
    for link in links:
        href = link.get('href')
        icon_class = link.select_one('i')
        if href and icon_class:
            platform = icon_class['class'][-1].replace('lp-', '')
            social_links.append({
                "platform": platform,
                "link": href
            })
    if social_links:
        data_card["Social_Links"] = social_links

    history_section = info_box.select('div.infobox-center table tbody tr')
    history = []
    for row in history_section:
        tds = row.select('td')
        if len(tds) < 2:
            continue
        date_text = tds[0].get_text(strip=True)
        from_date, to_date = (map(str.strip, date_text.split('—')) if '—' in date_text else (date_text.strip(), ''))
        team_link = tds[1].select_one('a')
        team_name = team_link.get('title') if team_link else tds[1].get_text(strip=True)
        note_span = tds[1].select_one('span')
        note = note_span.get_text(strip=True).strip("()") if note_span else ""
        history.append({
            "From": from_date,
            "To": to_date,
            "Team": team_name,
            "Note": note
        })
    if history:
        data_card["History"] = history

    upcoming_matches = []
    matches_section = soup.select('table.infobox_matches_content')
    for table in matches_section:
        rows = table.select('tr')
        if len(rows) < 2:
            continue
        row1, row2 = rows[0], rows[1]

        team1_td = row1.select_one('td.team-left')
        team2_td = row1.select_one('td.team-right')
        versus_td = row1.select_one('td.versus')
        if not team1_td or not team2_td or not versus_td:
            continue

        team1_name_tag = team1_td.select_one('a[title]')
        team1_name = team1_name_tag.get_text(strip=True) if team1_name_tag else "Unknown Team 1"
        team1_img_tag = team1_td.select_one('img')
        team1_logo = BASE_URL + team1_img_tag['src'] if team1_img_tag else None

        team2_name_tag = team2_td.select_one('.team-template-text a[title]')
        team2_name = team2_name_tag.get_text(strip=True) if team2_name_tag else team2_td.get_text(strip=True) or "Unknown Team 2"
        team2_img_tag = team2_td.select_one('img')
        team2_logo = BASE_URL + team2_img_tag['src'] if team2_img_tag else None

        score = versus_td.select_one('div')
        score_text = score.get_text(strip=True) if score else ""

        bo_text = versus_td.select_one('abbr')
        bo_format = bo_text.get('title') if bo_text else ""

        timestamp_elem = row2.select_one("span.timer-object")
        if timestamp_elem and timestamp_elem.has_attr("data-timestamp"):
            timestamp = int(timestamp_elem["data-timestamp"])
            match_time = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
        else:
            match_time = "TBD"

        tournament_div = row2.select_one('div[style*="white-space:nowrap"]')
        tournament_name = ""
        tournament_logo = ""
        if tournament_div:
            tournament_a = tournament_div.select_one('a')
            tournament_name = tournament_a.get('title') if tournament_a else ""
            tournament_img_tag = tournament_div.select_one('img')
            if tournament_img_tag and tournament_img_tag.get('src'):
                tournament_logo = BASE_URL + tournament_img_tag['src']

        upcoming_matches.append({
            "team1": team1_name,
            "team1_logo": team1_logo,
            "team2": team2_name,
            "team2_logo": team2_logo,
            "match_time": match_time,
            "score": score_text,
            "bo": bo_format,
            "tournament": tournament_name,
            "tournament_logo": tournament_logo
        })

    if upcoming_matches:
        data_card["Upcoming_Matches"] = upcoming_matches

    upcoming_tournaments = []
    tournaments_header = soup.find('div', class_='infobox-header', string='Upcoming Tournaments')
    if tournaments_header:
        for table in tournaments_header.find_all_next('table', class_='infobox_matches_content'):
            versus_td = table.select_one('td.versus')
            tournament_name = ""
            tournament_logo = ""
            tournament_link = versus_td.select_one('a') if versus_td else None
            if tournament_link:
                tournament_name = tournament_link.get('title') or tournament_link.text.strip()
                img_tag = versus_td.select_one('img')
                if img_tag and img_tag.get('src'):
                    tournament_logo = BASE_URL + img_tag['src']

            date_td = table.select_one('td.match-filler div')
            tournament_dates = date_td.get_text(strip=True) if date_td else ""

            status_span = table.select_one('span[style*="font-size"]')
            tournament_status = "ONGOING" if status_span and "ONGOING" in status_span.text else "UPCOMING"

            upcoming_tournaments.append({
                "tournament_name": tournament_name,
                "tournament_logo": tournament_logo,
                "dates": tournament_dates,
                "status": tournament_status
            })

    if upcoming_tournaments:
        data_card["Upcoming_Tournaments"] = upcoming_tournaments

    achievements = []
    achievements_header = soup.find('span', {'id': 'Achievements'})
    if achievements_header:
        current_element = achievements_header
        while current_element:
            current_element = current_element.find_next()
            if current_element.name == 'table' and 'wikitable' in current_element.get('class', []):
                table = current_element
                break

        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all(['td', 'th'])
                if len(cols) < 9:
                    continue

                date = cols[0].get_text(strip=True)
                place = cols[1].get_text(strip=True)
                tier = cols[2].get_text(strip=True)
                tournament = cols[4].get_text(strip=True)

                tournament_logo = None
                img_tag = cols[3].find('img')
                if img_tag and img_tag.get('src'):
                    tournament_logo = BASE_URL + img_tag['src']

                team_logo = None
                team_img_tag = cols[5].find('img')
                if team_img_tag and team_img_tag.get('src'):
                    team_logo = BASE_URL + team_img_tag['src']

                result = cols[6].get_text(strip=True)

                opponent_logo = None
                opponent_img_tag = cols[7].find('img')
                if opponent_img_tag and opponent_img_tag.get('src'):
                    opponent_logo = BASE_URL + opponent_img_tag['src']

                prize = cols[8].get_text(strip=True)

                achievements.append({
                    "Date": date,
                    "Place": place,
                    "Tier": tier,
                    "Tournament": tournament,
                    "Tournament_Logo": tournament_logo,
                    "Team_Logo": team_logo,
                    "Result": result,
                    "Opponent_Logo": opponent_logo,
                    "Prize": prize
                })
    if achievements:
        data_card["Achievements"] = achievements

    return data_card, player_page_name