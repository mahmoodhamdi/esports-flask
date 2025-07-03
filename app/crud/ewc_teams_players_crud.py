import json
import hashlib
from app.db import get_connection

def compute_hash(data_dict):
    json_str = json.dumps(data_dict, sort_keys=True)
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()

def get_teams_players(game: str, tournament: str, team_name: str = None, placement: str = None) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    query = '''
        SELECT team_name AS Team, placement AS Placement, tournament_logo AS Tournament_Logo, 
               years AS Years, players
        FROM ewc_teams_players
        WHERE game = ? AND tournament = ?
    '''
    params = [game, tournament]
    if team_name:
        query += ' AND team_name = ?'
        params.append(team_name)
    if placement:
        query += ' AND placement = ?'
        params.append(placement)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    teams_data = []
    for row in rows:
        team_data = dict(row)
        team_data['Players'] = json.loads(team_data.pop('players'))
        teams_data.append(team_data)
    return teams_data

def get_all_players(player_role: str = None, player_country: str = None, has_won_before: bool = None) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT game, tournament, team_name AS Team, placement AS Placement, 
               tournament_logo AS Tournament_Logo, years AS Years, players
        FROM ewc_teams_players
    ''')
    rows = cursor.fetchall()
    conn.close()
    all_players = []
    for row in rows:
        team_data = dict(row)
        players = json.loads(team_data.pop('players'))
        for player in players:
            if player_role and player['Role'] != player_role:
                continue
            if player_country and player['Country'] != player_country:
                continue
            if has_won_before is not None and player['HasWonBefore'] != has_won_before:
                continue
            player_data = {
                'Game': team_data['game'],
                'Tournament': team_data['tournament'],
                'Team': team_data['Team'],
                'Placement': team_data.get('Placement'),
                'Tournament_Logo': team_data.get('Tournament_Logo'),
                'Years': team_data.get('Years'),
                'Player': player
            }
            all_players.append(player_data)
    return all_players

def save_teams_players(game: str, tournament: str, teams_data: list[dict]) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for team in teams_data:
            team_name = team['Team']
            placement = team.get('Placement')
            tournament_logo = team.get('Tournament_Logo')
            years = team.get('Years')
            players_json = json.dumps(team.get('Players', []))
            hash_value = compute_hash(team)
            cursor.execute('''
                INSERT OR REPLACE INTO ewc_teams_players
                (game, tournament, team_name, placement, tournament_logo, years, players, hash_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (game, tournament, team_name, placement, tournament_logo, years, players_json, hash_value))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving teams players: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()