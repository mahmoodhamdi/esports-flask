from flask import Blueprint, request, jsonify
from app.crud.ewc_teams_players_crud import get_teams_players, save_teams_players, get_all_players
from app.ewc_teams_players import fetch_teams_players

ewc_teams_players_bp = Blueprint('ewc_teams_players', __name__)

def filter_players(players, role=None, country=None, has_won_before=None):
    filtered = players
    if role:
        filtered = [p for p in filtered if p['Role'] == role]
    if country:
        filtered = [p for p in filtered if p['Country'] == country]
    if has_won_before is not None:
        filtered = [p for p in filtered if p['HasWonBefore'] == has_won_before]
    return filtered

def filter_all_players(all_players, role=None, country=None, has_won_before=None):
    filtered = all_players
    if role:
        filtered = [p for p in filtered if p['Player']['Role'] == role]
    if country:
        filtered = [p for p in filtered if p['Player']['Country'] == country]
    if has_won_before is not None:
        filtered = [p for p in filtered if p['Player']['HasWonBefore'] == has_won_before]
    return filtered

def paginate(data, page, per_page):
    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = data[start:end]
    total_pages = (total + per_page - 1) // per_page
    return {
        'data': paginated_data,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        }
    }

@ewc_teams_players_bp.route('/ewc_teams_players', methods=['GET'])
def ewc_teams_players():
    game = request.args.get('game')
    tournament = request.args.get('tournament')
    live = request.args.get('live', 'false').lower() == 'true'
    team_name = request.args.get('team_name')
    placement = request.args.get('placement')
    player_role = request.args.get('player_role')
    player_country = request.args.get('player_country')
    has_won_before_str = request.args.get('has_won_before')
    has_won_before = None
    if has_won_before_str:
        has_won_before = has_won_before_str.lower() == 'true'
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    if not game or not tournament:
        return jsonify({"error": "Missing 'game' or 'tournament' parameter"}), 400

    if live:
        try:
            teams_data = fetch_teams_players(game, tournament)
            if not teams_data:
                return jsonify({"error": "No data fetched from API"}), 500
            if not save_teams_players(game, tournament, teams_data):
                return jsonify({"error": "Failed to save data to database"}), 500
        except Exception as e:
            return jsonify({"error": f"API fetch failed: {str(e)}"}), 500

    teams_data = get_teams_players(game, tournament, team_name, placement)

    filtered_teams = []
    for team in teams_data:
        filtered_players = filter_players(team['Players'], player_role, player_country, has_won_before)
        if filtered_players:
            team_copy = team.copy()
            team_copy['Players'] = filtered_players
            filtered_teams.append(team_copy)

    paginated = paginate(filtered_teams, page, per_page)
    return jsonify(paginated)

@ewc_teams_players_bp.route('/ewc_players', methods=['GET'])
def ewc_players():
    game = request.args.get('game')
    tournament = request.args.get('tournament')
    player_role = request.args.get('player_role')
    player_country = request.args.get('player_country')
    has_won_before_str = request.args.get('has_won_before')
    has_won_before = None
    if has_won_before_str:
        has_won_before = has_won_before_str.lower() == 'true'
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    if not game or not tournament:
        return jsonify({"error": "Missing 'game' or 'tournament' parameter"}), 400

    teams_data = get_teams_players(game, tournament)

    all_players = []
    for team in teams_data:
        for player in team['Players']:
            player_data = {
                'Team': team['Team'],
                'Placement': team.get('Placement'),
                'Tournament': tournament,
                'Tournament_Logo': team.get('Tournament_Logo'),
                'Years': team.get('Years'),
                'Player': player
            }
            all_players.append(player_data)

    filtered_players = filter_all_players(all_players, player_role, player_country, has_won_before)

    paginated = paginate(filtered_players, page, per_page)
    return jsonify(paginated)

# @ewc_teams_players_bp.route('/all_players', methods=['GET'])
# def all_players():
#     player_role = request.args.get('player_role')
#     player_country = request.args.get('player_country')
#     has_won_before_str = request.args.get('has_won_before')
#     has_won_before = None
#     if has_won_before_str:
#         has_won_before = has_won_before_str.lower() == 'true'
#     page = int(request.args.get('page', 1))
#     per_page = int(request.args.get('per_page', 10))

#     all_players = get_all_players(player_role, player_country, has_won_before)
#     filtered_players = filter_all_players(all_players, player_role, player_country, has_won_before)

#     paginated = paginate(filtered_players, page, per_page)
#     return jsonify(paginated)

@ewc_teams_players_bp.route('/all_players', methods=['GET'])
def all_players():
    player_role = request.args.get('player_role')
    player_country = request.args.get('player_country')
    has_won_before_str = request.args.get('has_won_before')
    has_won_before = None
    if has_won_before_str:
        has_won_before = has_won_before_str.lower() == 'true'

    all_players = get_all_players(player_role, player_country, has_won_before)
    filtered_players = filter_all_players(all_players, player_role, player_country, has_won_before)

    # تعطيل الـ pagination بإرجاع كل العناصر مرة واحدة مع الحفاظ على نفس شكل الـ response
    page = 1
    per_page = len(filtered_players) if filtered_players else 1  # عشان ميطلعش صفر ويتسبب في قسمة على صفر

    paginated = paginate(filtered_players, page, per_page)
    return jsonify(paginated)
