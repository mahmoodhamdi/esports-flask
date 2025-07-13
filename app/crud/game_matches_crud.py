import sqlite3
from app.db import get_connection
from collections import defaultdict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_game_matches(game=None, status=None, tournament=None, day=None, page=1, per_page=10):
    """Fetch matches from the database with filters, grouped by tournament and game, with pagination."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        conditions = []
        params = []

        if game:
            conditions.append('game = ?')
            params.append(game)
        if status:
            conditions.append('status = ?')
            params.append(status)
        if tournament:
            if isinstance(tournament, list):
                placeholders = ','.join(['?'] * len(tournament))
                conditions.append(f'tournament_name IN ({placeholders})')
                params.extend(tournament)
            else:
                conditions.append('tournament_name = ?')
                params.append(tournament)
        if day:
            try:
                datetime.strptime(day, "%Y-%m-%d")  # Validate format
                conditions.append('match_date = ?')
                params.append(day)
            except ValueError as e:
                logger.error(f"Invalid day format '{day}': {e}")
                raise ValueError("Day parameter must be in YYYY-MM-DD format")

        # First, get the total count of tournaments for pagination
        count_query = '''
            SELECT COUNT(DISTINCT tournament_name) as total_tournaments
            FROM game_matches
        '''
        if conditions:
            count_query += ' WHERE ' + ' AND '.join(conditions)
        
        cursor.execute(count_query, params)
        total_tournaments = cursor.fetchone()['total_tournaments']

        # Get distinct tournaments with pagination
        tournaments_query = '''
            SELECT DISTINCT tournament_name, tournament_icon
            FROM game_matches
        '''
        if conditions:
            tournaments_query += ' WHERE ' + ' AND '.join(conditions)
        
        # Add pagination to tournament selection
        tournaments_query += ' ORDER BY tournament_name ASC LIMIT ? OFFSET ?'
        offset = (page - 1) * per_page
        tournament_params = params + [per_page, offset]
        
        cursor.execute(tournaments_query, tournament_params)
        tournaments_page = cursor.fetchall()

        if not tournaments_page:
            conn.close()
            return {
                "tournaments": [],
                "total": total_tournaments,
                "page": page,
                "per_page": per_page
            }

        # Get tournament names for the current page
        tournament_names = [t['tournament_name'] for t in tournaments_page]
        
        # Build the main query to fetch matches only for tournaments on current page
        main_conditions = conditions.copy()
        main_params = params.copy()
        
        # Add tournament filter for current page
        tournament_placeholders = ','.join(['?'] * len(tournament_names))
        main_conditions.append(f'tournament_name IN ({tournament_placeholders})')
        main_params.extend(tournament_names)

        matches_query = '''
            SELECT id, game, status, tournament_name, team1_name, team2_name, 
                   match_time, score, stream_link, team1_logo, team2_logo, tournament_icon 
            FROM game_matches
        '''
        if main_conditions:
            matches_query += ' WHERE ' + ' AND '.join(main_conditions)
        matches_query += ' ORDER BY tournament_name ASC, match_time ASC'

        logger.debug(f"Executing matches query: {matches_query} with params: {main_params}")
        cursor.execute(matches_query, main_params)
        matches = [dict(row) for row in cursor.fetchall()]

        # Debug: Log the matches found for day filtering
        if day:
            logger.debug(f"Found {len(matches)} matches for day {day}")
            for match in matches[:3]:  # Log first 3 matches
                logger.debug(f"Match: {match['team1_name']} vs {match['team2_name']} at {match['match_time']}")

        conn.close()

        # Group matches by tournament and game
        tournaments = defaultdict(lambda: {'tournament_image': None, 'games': defaultdict(list)})
        for match in matches:
            tournament_name = match['tournament_name']
            if tournaments[tournament_name]['tournament_image'] is None:
                tournaments[tournament_name]['tournament_image'] = match['tournament_icon']
            match_data = {
                'id': match['id'],
                'match_time': match['match_time'],
                'score': match['score'],
                'status': match['status'],
                'team1_name': match['team1_name'],
                'team2_name': match['team2_name'],
                'team1_image': match['team1_logo'],
                'team2_image': match['team2_logo'],
                'stream_link': match['stream_link']
            }
            tournaments[tournament_name]['games'][match['game']].append(match_data)
        
        # Convert to list format maintaining the order from tournaments_page
        tournaments_list = []
        for tournament_data in tournaments_page:
            tournament_name = tournament_data['tournament_name']
            if tournament_name in tournaments:
                games_list = []
                for game_name, game_matches in tournaments[tournament_name]['games'].items():
                    games_list.append({
                        "game": game_name,
                        "matches": game_matches
                    })
                tournaments_list.append({
                    "tournament_name": tournament_name,
                    "tournament_image": tournaments[tournament_name]['tournament_image'],
                    "games": games_list
                })

        logger.info(f"Returning {len(tournaments_list)} tournaments (page {page}, per_page {per_page}) out of {total_tournaments} total tournaments")
        return {
            "tournaments": tournaments_list,
            "total": total_tournaments,
            "page": page,
            "per_page": per_page
        }
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        raise