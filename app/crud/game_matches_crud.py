import sqlite3
from app.db import get_connection
from collections import defaultdict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_game_matches(game=None, status=None, tournament=None, day=None):
    """Fetch matches from the database with filters, grouped by tournament and game."""
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

        query = 'SELECT id, game, status, tournament_name, team1_name, team2_name, match_time, score, stream_link FROM game_matches'
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY match_time ASC'

        logger.debug(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        matches = [dict(row) for row in cursor.fetchall()]

        # Debug: Log the matches found for day filtering
        if day:
            logger.debug(f"Found {len(matches)} matches for day {day}")
            for match in matches[:3]:  # Log first 3 matches
                logger.debug(f"Match: {match['team1_name']} vs {match['team2_name']} at {match['match_time']}")

        conn.close()

        tournaments = defaultdict(lambda: defaultdict(list))
        for match in matches:
            match_data = {
                'id': match['id'],
                'match_time': match['match_time'],
                'score': match['score'],
                'status': match['status'],
                'team1_name': match['team1_name'],
                'team2_name': match['team2_name'],
                'stream_link': match['stream_link']
            }
            tournaments[match['tournament_name']][match['game']].append(match_data)
        
        tournaments_list = []
        for tournament_name, games in tournaments.items():
            games_list = []
            for game_name, game_matches in games.items():
                games_list.append({
                    "game": game_name,
                    "matches": game_matches
                })
            tournaments_list.append({
                "tournament_name": tournament_name,
                "games": games_list
            })
        logger.info(f"Returning {len(tournaments_list)} tournaments with {sum(len(g['matches']) for t in tournaments_list for g in t['games'])} matches")
        return tournaments_list
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        raise