import sqlite3
import logging

logger = logging.getLogger(__name__)

def get_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect("news.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_game_matches_db():
    """Initialize the SQLite database with tournaments, matches, and matches_games tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create tournaments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT NOT NULL,
                name TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                icon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create matches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                match_id TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                team1 TEXT,
                team1_url TEXT,
                logo1_light TEXT,
                logo1_dark TEXT,
                team2 TEXT,
                team2_url TEXT,
                logo2_light TEXT,
                logo2_dark TEXT,
                timestamp INTEGER,
                match_time TEXT,
                format TEXT,
                score TEXT,
                stream_links TEXT,
                details_link TEXT,
                group_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
            )
        ''')

        # Create matches_games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches_games (
                match_id TEXT NOT NULL,
                game TEXT NOT NULL,
                PRIMARY KEY (match_id, game),
                FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
            )
        ''')

        # Create indexes for matches
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_match_id ON matches(match_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_timestamp ON matches(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_tournament_id ON matches(tournament_id)')

        # Create index for matches_games
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_matches_games_game ON matches_games(game)')

        conn.commit()
        logger.info("Game matches database initialized successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Game matches database initialization error: {str(e)}")
        raise
    finally:
        conn.close()