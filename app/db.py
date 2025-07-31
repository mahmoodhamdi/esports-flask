import sqlite3
import os
import logging
import hashlib
logger = logging.getLogger(__name__)

def get_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect("news.db")
    conn.row_factory = sqlite3.Row
    return conn

def generate_match_uid(game, team1, team2, match_time, details_link):
    key = f"{game}_{team1}_{team2}_{match_time}_{details_link}"
    return hashlib.md5(key.encode()).hexdigest()

def init_db():
    """Initialize the SQLite database with all required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create weeks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weeks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        
        # Create games table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games_in_week (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_id INTEGER NOT NULL,
                game_name TEXT NOT NULL,
                FOREIGN KEY (week_id) REFERENCES weeks(id)
            )
        """)
        
        # Create settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings_in_week (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Create matches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT,
                status TEXT,
                tournament TEXT,
                tournament_link TEXT,
                tournament_icon TEXT,
                team1 TEXT,
                team1_url TEXT,                        
                logo1_light TEXT,
                logo1_dark TEXT,
                team2 TEXT,
                team2_url TEXT,                        
                logo2_light TEXT,
                logo2_dark TEXT,
                score TEXT,
                match_time TEXT,
                format TEXT,
                stream_links TEXT,                     
                details_link TEXT,                     
                match_group TEXT
            )
        ''')
        # Try to add uid column (skip if already exists)
        try:
            cursor.execute("ALTER TABLE matches ADD COLUMN uid TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                raise  # Raise if it's a different error

        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_matches_uid ON matches(uid);
        ''')
        
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game, team_name)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_information (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT NOT NULL,
                player_page_name TEXT NOT NULL,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game, player_page_name)
            )
        ''')        
        # Create team_information table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_information (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT NOT NULL,
                team_page_name TEXT NOT NULL,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game, team_page_name)
            )
        ''')

        # Create search_logs table for query logging
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                search_type TEXT,
                execution_time REAL NOT NULL,
                result_count INTEGER NOT NULL,
                page INTEGER DEFAULT 1,
                per_page INTEGER DEFAULT 10,
                filter_field TEXT,
                filter_value TEXT,
                user_ip TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create FTS5 virtual tables for full-text search
        # News FTS table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS news_fts USING fts5(
                title, description, writer, content=news, content_rowid=id
            )
        ''')
        
     
        
     
        # Games FTS table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS games_fts USING fts5(
                game_name, genre, platform, description, content=games, content_rowid=id
            )
        ''')
        
       

        # Prize distribution FTS table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS prize_distribution_fts USING fts5(
                place, prize, participants, content=prize_distribution, content_rowid=id
            )
        ''')

        # EWC info FTS table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS ewc_info_fts USING fts5(
                header, series, organizers, location, prize_pool, liquipedia_tier, content=ewc_info, content_rowid=id
            )
        ''')

       
        # Transfers FTS table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS transfers_fts USING fts5(
                game, player_name, old_team_name, new_team_name, content=transfers, content_rowid=id
            )
        ''')

         

        # EWC teams players FTS table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS ewc_teams_players_fts USING fts5(
                game, team_name, placement, tournament, players, content=ewc_teams_players, content_rowid=id
            )
        ''')

        # Player information FTS table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS player_information_fts USING fts5(
                game, player_page_name, data, content=player_information, content_rowid=id
            )
        ''')

        # Team information FTS table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS team_information_fts USING fts5(
                game, team_page_name, data, content=team_information, content_rowid=id
            )
        ''')

        # Create triggers to keep FTS tables in sync
        # News triggers
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS news_ai AFTER INSERT ON news BEGIN
                INSERT INTO news_fts(rowid, title, description, writer) 
                VALUES (new.id, new.title, new.description, new.writer);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS news_ad AFTER DELETE ON news BEGIN
                INSERT INTO news_fts(news_fts, rowid, title, description, writer) 
                VALUES('delete', old.id, old.title, old.description, old.writer);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS news_au AFTER UPDATE ON news BEGIN
                INSERT INTO news_fts(news_fts, rowid, title, description, writer) 
                VALUES('delete', old.id, old.title, old.description, old.writer);
                INSERT INTO news_fts(rowid, title, description, writer) 
                VALUES (new.id, new.title, new.description, new.writer);
            END
        ''')

        
 
        # Games triggers
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS games_ai AFTER INSERT ON games BEGIN
                INSERT INTO games_fts(rowid, game_name, genre, platform, description) 
                VALUES (new.id, new.game_name, new.genre, new.platform, new.description);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS games_ad AFTER DELETE ON games BEGIN
                INSERT INTO games_fts(games_fts, rowid, game_name, genre, platform, description) 
                VALUES('delete', old.id, old.game_name, old.genre, old.platform, old.description);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS games_au AFTER UPDATE ON games BEGIN
                INSERT INTO games_fts(games_fts, rowid, game_name, genre, platform, description) 
                VALUES('delete', old.id, old.game_name, old.genre, old.platform, old.description);
                INSERT INTO games_fts(rowid, game_name, genre, platform, description) 
                VALUES (new.id, new.game_name, new.genre, new.platform, new.description);
            END
        ''')

     
        # Prize distribution triggers
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS prize_distribution_ai AFTER INSERT ON prize_distribution BEGIN
                INSERT INTO prize_distribution_fts(rowid, place, prize, participants) 
                VALUES (new.id, new.place, new.prize, new.participants);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS prize_distribution_ad AFTER DELETE ON prize_distribution BEGIN
                INSERT INTO prize_distribution_fts(prize_distribution_fts, rowid, place, prize, participants) 
                VALUES('delete', old.id, old.place, old.prize, old.participants);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS prize_distribution_au AFTER UPDATE ON prize_distribution BEGIN
                INSERT INTO prize_distribution_fts(prize_distribution_fts, rowid, place, prize, participants) 
                VALUES('delete', old.id, old.place, old.prize, old.participants);
                INSERT INTO prize_distribution_fts(rowid, place, prize, participants) 
                VALUES (new.id, new.place, new.prize, new.participants);
            END
        ''')

        # EWC info triggers
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS ewc_info_ai AFTER INSERT ON ewc_info BEGIN
                INSERT INTO ewc_info_fts(rowid, header, series, organizers, location, prize_pool, liquipedia_tier) 
                VALUES (new.id, new.header, new.series, new.organizers, new.location, new.prize_pool, new.liquipedia_tier);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS ewc_info_ad AFTER DELETE ON ewc_info BEGIN
                INSERT INTO ewc_info_fts(ewc_info_fts, rowid, header, series, organizers, location, prize_pool, liquipedia_tier) 
                VALUES('delete', old.id, old.header, old.series, old.organizers, old.location, old.prize_pool, old.liquipedia_tier);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS ewc_info_au AFTER UPDATE ON ewc_info BEGIN
                INSERT INTO ewc_info_fts(ewc_info_fts, rowid, header, series, organizers, location, prize_pool, liquipedia_tier) 
                VALUES('delete', old.id, old.header, old.series, old.organizers, old.location, old.prize_pool, old.liquipedia_tier);
                INSERT INTO ewc_info_fts(rowid, header, series, organizers, location, prize_pool, liquipedia_tier) 
                VALUES (new.id, new.header, new.series, new.organizers, new.location, new.prize_pool, new.liquipedia_tier);
            END
        ''')

        # Transfers triggers
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS transfers_ai AFTER INSERT ON transfers BEGIN
                INSERT INTO transfers_fts(rowid, game, player_name, old_team_name, new_team_name) 
                VALUES (new.id, new.game, new.player_name, new.old_team_name, new.new_team_name);
            END
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                logo_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                game_name TEXT NOT NULL,
                logo_mode TEXT,
                logo_url TEXT,
                FOREIGN KEY (team_id) REFERENCES new_teams(id) ON DELETE CASCADE
            )
        ''')
      

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS transfers_ad AFTER DELETE ON transfers BEGIN
                INSERT INTO transfers_fts(transfers_fts, rowid, game, player_name, old_team_name, new_team_name) 
                VALUES('delete', old.id, old.game, old.player_name, old.old_team_name, old.new_team_name);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS transfers_au AFTER UPDATE ON transfers BEGIN
                INSERT INTO transfers_fts(transfers_fts, rowid, game, player_name, old_team_name, new_team_name) 
                VALUES('delete', old.id, old.game, old.player_name, old.old_team_name, old.new_team_name);
                INSERT INTO transfers_fts(rowid, game, player_name, old_team_name, new_team_name) 
                VALUES (new.id, new.game, new.player_name, new.old_team_name, new.new_team_name);
            END
        ''')

        conn.commit()
        logger.info("Database initialized successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise
    finally:
        conn.close()
