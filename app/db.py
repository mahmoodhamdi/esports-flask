import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def get_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect("news.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database with all required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create news table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                writer TEXT NOT NULL,
                thumbnail_url TEXT,
                news_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create prize_distribution table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prize_distribution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place TEXT,
                place_logo TEXT,
                prize TEXT,
                participants TEXT,
                logo_team TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create ewc_info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ewc_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                header TEXT,
                series TEXT,
                organizers TEXT,
                location TEXT,
                prize_pool TEXT,
                start_date TEXT,
                end_date TEXT,
                liquipedia_tier TEXT,
                logo_light TEXT,
                logo_dark TEXT,
                location_logo TEXT,
                social_links TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_name TEXT,
                genre TEXT,
                platform TEXT,
                release_date TEXT,
                description TEXT,
                       
                logo_url TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create group_matches table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game TEXT,
            tournament TEXT,
            group_name TEXT,
            team1_name TEXT,
            team1_logo TEXT,
            team2_name TEXT,
            team2_logo TEXT,
            match_time TEXT,
            score TEXT
        )
    ''')
        
        # Create teams table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT,
                logo_url TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                link TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create matches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT,
                match_date TEXT,
                group_name TEXT,
                team1_name TEXT,
                team1_logo TEXT,
                team2_name TEXT,
                team2_logo TEXT,
                match_time TEXT,
                score TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''') 
        
        # Create transfers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_id TEXT UNIQUE,
                game TEXT,
                date TEXT,
                player_name TEXT,
                player_flag TEXT,
                old_team_name TEXT,
                old_team_logo_light TEXT,
                old_team_logo_dark TEXT,
                new_team_name TEXT,
                new_team_logo_light TEXT,
                new_team_logo_dark TEXT,
                hash_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create global_matches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT NOT NULL,
                tournament TEXT NOT NULL,
                group_name TEXT,
                team1_name TEXT,
                team1_logo TEXT,
                team2_name TEXT,
                team2_logo TEXT,
                match_time TEXT,
                score TEXT,
                status TEXT DEFAULT 'scheduled',
                hash_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise
    finally:
        conn.close()

def reset_db_sequence():
    """Reset the SQLite sequence for all tables"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM sqlite_sequence 
            WHERE name IN ('news', 'teams', 'events', 'ewc_info', 'games', 'matches', 'transfers', 'prize_distribution', 'global_matches')
        """)
        conn.commit()
        logger.debug("Reset SQLite sequence for all tables")
    except sqlite3.Error as e:
        logger.error(f"Failed to reset SQLite sequence: {str(e)}")
        raise
    finally:
        conn.close()

        # Create ewc_teams_players table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ewc_teams_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT NOT NULL,
                team_name TEXT NOT NULL,
                placement TEXT,
                tournament TEXT,
                tournament_logo TEXT,
                years TEXT,
                players TEXT, -- Storing players as JSON string
                hash_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

