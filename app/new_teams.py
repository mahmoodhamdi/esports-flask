import json
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fetch_teams_from_json():
    """
    Load and parse teams_ewc.json, returning teams in the expected format.
    """
    try:
        if not os.path.exists('teams_ewc.json'):
            logger.error("teams_ewc.json not found in project root")
            return []
        
        with open('teams_ewc.json', 'r') as file:
            data = json.load(file)
        
        if not isinstance(data, list):
            logger.error("Invalid JSON structure: expected a list of teams")
            return []
        
        teams_data = []
        for team in data:
            if not isinstance(team, dict) or 'team_name' not in team:
                logger.warning(f"Skipping invalid team entry: {team}")
                continue
            
            team_data = {
                'name': team['team_name'],
                'logo_url': team.get('logo_url', ''),
                'games': []
            }
            games = team.get('games', [])
            if not isinstance(games, list):
                logger.warning(f"No valid games for team {team['team_name']}")
            else:
                for game in games:
                    if not isinstance(game, dict) or 'game_name' not in game:
                        logger.warning(f"Skipping invalid game entry for team {team['team_name']}: {game}")
                        continue
                    game_data = {
                        'game_name': game['game_name'],
                        'game_logos': []
                    }
                    logos = game.get('game_logos', [])
                    if not isinstance(logos, list):
                        logger.warning(f"No valid game_logos for game {game['game_name']} in team {team['team_name']}")
                    else:
                        for logo in logos:
                            if not isinstance(logo, dict) or 'mode' not in logo or 'url' not in logo:
                                logger.warning(f"Skipping invalid logo entry for game {game['game_name']} in team {team['team_name']}: {logo}")
                                continue
                            game_data['game_logos'].append({
                                'mode': logo['mode'],
                                'url': logo['url']
                            })
                    team_data['games'].append(game_data)
            teams_data.append(team_data)
            logger.debug(f"Parsed team: {team_data['name']}, games: {len(team_data['games'])}")
        
        logger.info(f"Successfully parsed {len(teams_data)} teams from JSON")
        return teams_data
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in fetch_teams_from_json: {e}")
        return []