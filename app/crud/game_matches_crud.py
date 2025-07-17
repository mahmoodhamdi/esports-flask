import json
from app.game_matches_init_db import get_connection

def get_tournament_by_link(conn, link):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tournaments WHERE link = ?", (link,))
    return cursor.fetchone()

def insert_or_update_match_game(conn, match_id, game):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO matches_games (match_id, game)
        VALUES (?, ?)
    ''', (match_id, game))
    conn.commit()

def get_grouped_matches(conn, game=None, day=None, tournament=None, status=None, page=1, per_page=10):
    offset = (page - 1) * per_page
    query = '''
        SELECT m.*, t.name as tournament_name, t.game as primary_game, t.link as tournament_link, t.icon as tournament_icon, mg.game
        FROM matches m
        JOIN tournaments t ON m.tournament_id = t.id
        JOIN matches_games mg ON m.match_id = mg.match_id
        WHERE 1=1
    '''
    params = []
    
    if game:
        query += " AND mg.game IN ({})".format(','.join(['?'] * len(game)))
        params.extend(game)
    
    if day:
        query += " AND DATE(m.timestamp, 'unixepoch') IN ({})".format(','.join(['?'] * len(day)))
        params.extend(day)
    
    if tournament:
        query += " AND t.name IN ({})".format(','.join(['?'] * len(tournament)))
        params.extend(tournament)
    
    if status:
        query += " AND m.status = ?"
        params.append(status)
    
    query += " ORDER BY m.timestamp ASC"
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    matches = cursor.fetchall()
    
    count_query = '''
        SELECT COUNT(*)
        FROM matches m
        JOIN tournaments t ON m.tournament_id = t.id
        JOIN matches_games mg ON m.match_id = mg.match_id
        WHERE 1=1
    '''
    count_params = []
    if game:
        count_query += " AND mg.game IN ({})".format(','.join(['?'] * len(game)))
        count_params.extend(game)
    if day:
        count_query += " AND DATE(m.timestamp, 'unixepoch') IN ({})".format(','.join(['?'] * len(day)))
        count_params.extend(day)
    if tournament:
        count_query += " AND t.name IN ({})".format(','.join(['?'] * len(tournament)))
        count_params.extend(tournament)
    if status:
        count_query += " AND m.status = ?"
        count_params.append(status)
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]
    
    # Group matches by tournament and game
    tournaments = {}
    for match in matches:
        tournament_name = match['tournament_name']
        game_name = match['game']
        
        if tournament_name not in tournaments:
            tournaments[tournament_name] = {
                'tournament_name': tournament_name,
                'tournament_link': match['tournament_link'],
                'tournament_icon': match['tournament_icon'],
                'games': {}
            }
        
        if game_name not in tournaments[tournament_name]['games']:
            tournaments[tournament_name]['games'][game_name] = {
                'game': game_name,
                'matches': []
            }
        
        tournaments[tournament_name]['games'][game_name]['matches'].append({
            'id': match['id'],
            'match_id': match['match_id'],
            'status': match['status'],
            'team1': match['team1'],
            'team1_url': match['team1_url'],
            'logo1_light': match['logo1_light'],
            'logo1_dark': match['logo1_dark'],
            'team2': match['team2'],
            'team2_url': match['team2_url'],
            'logo2_light': match['logo2_light'],
            'logo2_dark': match['logo2_dark'],
            'timestamp': match['timestamp'],
            'match_time': match['match_time'],
            'format': match['format'],
            'score': match['score'],
            'stream_links': json.loads(match['stream_links']),
            'details_link': match['details_link'],
            'group_name': match['group_name'],
            'created_at': match['created_at'],
            'updated_at': match['updated_at']
        })
    
    # Convert to list for response
    grouped_matches = list(tournaments.values())
    for tournament in grouped_matches:
        tournament['games'] = list(tournament['games'].values())
    
    return grouped_matches, total