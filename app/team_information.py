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

def get_team_info(game: str, team_page_name: str) -> tuple[dict, str]:
    """Fetch team information from Liquipedia API."""
    html = get_html_from_api(game, team_page_name)
    if not html:
        return {}, team_page_name

    soup = BeautifulSoup(html, 'html.parser')
    data_card = {}

    info_box = soup.select_one('div.fo-nttax-infobox')
    if not info_box:
        print("Could not find team info box on the page.")
        return {}, team_page_name

    header = info_box.select_one('div.infobox-header')
    if header:
        data_card['Name'] = header.get_text(strip=True)

    team_img = info_box.select_one('div.infobox-image-wrapper img')
    if team_img and team_img.get('src'):
        data_card['team_Image'] = BASE_URL + team_img['src']

    desired_fields = {'Location', 'Region', 'Coach', 'Manager', 'Team Captain', 'Approx. Total Winnings'}
    team_info = {}
    rows = info_box.select('div.infobox-cell-2.infobox-description')
    for desc in rows:
        key = desc.text.strip().rstrip(':')
        value_div = desc.find_next_sibling()
        if not value_div or key not in desired_fields:
            continue
        entries = []
        texts = list(value_div.stripped_strings)
        imgs = value_div.select('img')
        for i, text in enumerate(texts):
            entry = {"text": text}
            if i < len(imgs) and imgs[i].get('src'):
                entry["image"] =(BASE_URL + imgs[i]['src'])
            else:
                entry["image"] = None
            entries.append(entry)
        team_info[key] = entries
    if team_info:
        data_card["Team_Information"] = team_info

    social_links = []
    links = info_box.select('div.infobox-center.infobox-icons a.external.text')
    for link in links:
        href = link.get('href')
        icon_class = link.select_one('i')
        if href and icon_class:
            platform = icon_class['class'][-1].replace('lp-', '')
            social_links.append({"platform": platform, "link": href})
    if social_links:
        data_card["Social_Links"] = social_links

    achievements_logos = []
    achievements_header = soup.find('div', class_='infobox-header', string='Achievements')
    if achievements_header:
        next_element = achievements_header.find_next()
        while next_element:
            img_tags = next_element.select('img')
            if img_tags:
                for img in img_tags:
                    if src := img.get('src'):
                        achievements_logos.append(BASE_URL + src)
                break
            next_element = next_element.find_next()
    if achievements_logos:
        data_card["Achievements_Logos"] = achievements_logos

    history = {}
    history_header_wrapper = soup.find('div', class_='infobox-header', string='History')
    if history_header_wrapper:
        parent_container = history_header_wrapper.find_parent('div')
        for sibling in parent_container.find_next_siblings('div'):
            if 'infobox-header' in sibling.get('class', []):
                break
            desc_div = sibling.select_one('div.infobox-cell-2.infobox-description')
            value_div = sibling.select_one('div[style]')
            if desc_div and value_div:
                key = desc_div.get_text(strip=True).rstrip(":")
                history[key] = value_div.get_text(strip=True)
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
        if not all([team1_td, team2_td, versus_td]):
            continue

        team1_name = (team1_td.select_one('a[title]') or team1_td.select_one('a') or team1_td).get('title', team1_td.get_text(strip=True))
        team1_logo = BASE_URL + team1_td.select_one('img')['src'] if team1_td.select_one('img') else None

        team2_name = (team2_td.select_one('a[title]') or team2_td.select_one('a') or team2_td).get('title', team2_td.get_text(strip=True))
        team2_logo = BASE_URL + team2_td.select_one('img')['src'] if team2_td.select_one('img') else None

        score = versus_td.select_one('div').get_text(strip=True) if versus_td.select_one('div') else ""
        bo_format = versus_td.select_one('abbr')['title'] if versus_td.select_one('abbr') else ""

        timestamp_elem = row2.select_one("span.timer-object")
        match_time = datetime.utcfromtimestamp(int(timestamp_elem["data-timestamp"])).strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp_elem and "data-timestamp" in timestamp_elem.attrs else "TBD"

        tournament_a = row2.select_one('a[title]')
        tournament_name = tournament_a.get('title') if tournament_a else ""
        tournament_logo = BASE_URL + (tournament_a or row2).select_one('img')['src'] if (tournament_a or row2).select_one('img') else ""

        upcoming_matches.append({
            "team1": team1_name, "team1_logo": team1_logo, "team2": team2_name, "team2_logo": team2_logo,
            "match_time": match_time, "score": score, "bo": bo_format, "tournament": tournament_name, "tournament_logo": tournament_logo
        })
    if upcoming_matches:
        data_card["Upcoming_Matches"] = upcoming_matches

    upcoming_tournaments = []
    tournaments_header = soup.find('div', class_='infobox-header', string='Upcoming Tournaments')
    if tournaments_header:
        for table in tournaments_header.find_all_next('table', class_='infobox_matches_content'):
            versus_td = table.select_one('td.versus')
            if not versus_td or not (tournament_link := versus_td.select_one('a')):
                continue
            tournament_name = tournament_link.get('title') or tournament_link.text.strip()
            tournament_logo = BASE_URL + versus_td.select_one('img')['src'] if versus_td.select_one('img') else ""
            date_td = table.select_one('td.match-filler div')
            tournament_dates = date_td.get_text(strip=True) if date_td else ""
            status_span = table.select_one('span[style*="font-size"]')
            tournament_status = "ONGOING" if status_span and "ONGOING" in status_span.text else "UPCOMING"
            upcoming_tournaments.append({
                "tournament_name": tournament_name, "tournament_logo": tournament_logo,
                "dates": tournament_dates, "status": tournament_status
            })
    if upcoming_tournaments:
        data_card["Upcoming_Tournaments"] = upcoming_tournaments

    # Note: Achievements parsing might be Dota 2-specific; adjust for other games if needed
    achievements = []
    achievements_header = soup.find('span', {'id': f'Results_of_{team_page_name.replace(" ", "_")}'})
    if achievements_header:
        content_div = achievements_header.find_next('div', class_='tabs-content')
        if content_div and (table := content_div.select_one('div.content1 table.wikitable')):
            for row in table.select('tbody tr'):
                cols = row.find_all('td')
                if len(cols) < 8:
                    continue
                achievements.append({
                    "Date": cols[0].get_text(strip=True),
                    "Place": cols[1].get_text(strip=True),
                    "Tier": cols[2].get_text(strip=True),
                    "Tournament": cols[4].get_text(strip=True),
                    "Tournament_Logo": BASE_URL + cols[3].select_one('img')['src'] if cols[3].select_one('img') else None,
                    "Result": cols[5].get_text(strip=True),
                    "Opponent_Logo": BASE_URL + cols[6].select_one('img')['src'] if cols[6].select_one('img') else None,
                    "Prize": cols[7].get_text(strip=True)
                })
    if achievements:
        data_card["Achievements"] = achievements

    return data_card, team_page_name