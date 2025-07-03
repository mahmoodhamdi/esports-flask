import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def get_connection():
    """Get database connection with row factory and optimized settings"""
    conn = sqlite3.connect("news.db", timeout=30.0)
    conn.row_factory = sqlite3.Row
    
    # Enable optimization settings
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
    conn.execute("PRAGMA synchronous=NORMAL")  # Better performance
    conn.execute("PRAGMA cache_size=10000")  # Increase cache
    conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
    conn.execute("PRAGMA mmap_size=134217728")  # 128MB memory mapping
    
    return conn

def create_indexes():
    """Create optimized indexes for search performance"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # News table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_title ON news(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_description ON news(description)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_writer ON news(writer)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_search ON news(title, description, writer)")
        
        # Teams table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(team_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_teams_updated_at ON teams(updated_at)")
        
        # Events table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_name ON events(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_updated_at ON events(updated_at)")
        
        # Games table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_name ON games(game_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_genre ON games(genre)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_platform ON games(platform)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_search ON games(game_name, genre, platform)")
        
        # Matches table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_team1 ON matches(team1_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_team2 ON matches(team2_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_game ON matches(game)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches(tournament)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_search ON matches(team1_name, team2_name, game)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_updated_at ON matches(updated_at)")
        
        # Group matches table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_matches_team1 ON group_matches(team1_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_matches_team2 ON group_matches(team2_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_matches_game ON group_matches(game)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_matches_tournament ON group_matches(tournament)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_matches_group ON group_matches(group_name)")
        
        # Global matches table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_matches_team1 ON global_matches(team1_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_matches_team2 ON global_matches(team2_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_matches_game ON global_matches(game)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_matches_tournament ON global_matches(tournament)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_matches_status ON global_matches(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_matches_created_at ON global_matches(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_matches_search ON global_matches(team1_name, team2_name, game)")
        
        # Transfers table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_player ON transfers(player_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_game ON transfers(game)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_date ON transfers(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_old_team ON transfers(old_team_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_new_team ON transfers(new_team_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_created_at ON transfers(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_unique_id ON transfers(unique_id)")
        
        # EWC teams players table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ewc_teams_game ON ewc_teams_players(game)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ewc_teams_name ON ewc_teams_players(team_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ewc_teams_tournament ON ewc_teams_players(tournament)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ewc_teams_created_at ON ewc_teams_players(created_at)")
        
        # Player information table indexes (for JSON search optimization)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_info_game ON player_information(game)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_info_name ON player_information(player_page_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_info_updated_at ON player_information(updated_at)")
        
        # Team information table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_info_game ON team_information(game)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_info_name ON team_information(team_page_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_info_updated_at ON team_information(updated_at)")
        
        # Prize distribution table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prize_place ON prize_distribution(place)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prize_updated_at ON prize_distribution(updated_at)")
        
        # EWC info table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ewc_info_series ON ewc_info(series)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ewc_info_location ON ewc_info(location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ewc_info_start_date ON ewc_info(start_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ewc_info_updated_at ON ewc_info(updated_at)")
        
        conn.commit()
        logger.info("Database indexes created successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Index creation error: {str(e)}")
        raise
    finally:
        conn.close()

def create_full_text_search_tables():
    """Create FTS (Full Text Search) virtual tables for better search performance"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create FTS table for news
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS news_fts USING fts5(
                title, description, writer, content=news, content_rowid=id
            )
        """)
        
        # Create FTS table for games
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS games_fts USING fts5(
                game_name, description, genre, platform, content=games, content_rowid=id
            )
        """)
        
        # Create triggers to keep FTS tables in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS news_fts_insert AFTER INSERT ON news BEGIN
                INSERT INTO news_fts(rowid, title, description, writer) 
                VALUES (new.id, new.title, new.description, new.writer);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS news_fts_delete AFTER DELETE ON news BEGIN
                INSERT INTO news_fts(news_fts, rowid, title, description, writer) 
                VALUES('delete', old.id, old.title, old.description, old.writer);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS news_fts_update AFTER UPDATE ON news BEGIN
                INSERT INTO news_fts(news_fts, rowid, title, description, writer) 
                VALUES('delete', old.id, old.title, old.description, old.writer);
                INSERT INTO news_fts(rowid, title, description, writer) 
                VALUES (new.id, new.title, new.description, new.writer);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS games_fts_insert AFTER INSERT ON games BEGIN
                INSERT INTO games_fts(rowid, game_name, description, genre, platform) 
                VALUES (new.id, new.game_name, new.description, new.genre, new.platform);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS games_fts_delete AFTER DELETE ON games BEGIN
                INSERT INTO games_fts(games_fts, rowid, game_name, description, genre, platform) 
                VALUES('delete', old.id, old.game_name, old.description, old.genre, old.platform);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS games_fts_update AFTER UPDATE ON games BEGIN
                INSERT INTO games_fts(games_fts, rowid, game_name, description, genre, platform) 
                VALUES('delete', old.id, old.game_name, old.description, old.genre, old.platform);
                INSERT INTO games_fts(rowid, game_name, description, genre, platform) 
                VALUES (new.id, new.game_name, new.description, new.genre, new.platform);
            END
        """)
        
        conn.commit()
        logger.info("FTS tables and triggers created successfully")
        
    except sqlite3.Error as e:
        logger.error(f"FTS table creation error: {str(e)}")
        # Don't raise here as FTS is optional
        logger.warning("Continuing without FTS support")
    finally:
        conn.close()

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
                tournament TEXT,
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
        
        # Create player_information table
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

        conn.commit()
        logger.info("Database tables created successfully")
        
        # Create indexes for better search performance
        create_indexes()
        
        # Create FTS tables for advanced search
        create_full_text_search_tables()
        
        logger.info("Database initialized successfully with optimizations")
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise
    finally:
        conn.close()

def optimize_database():
    """Run database optimization commands"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Analyze tables for query optimization
        cursor.execute("ANALYZE")
        
        # Rebuild indexes
        cursor.execute("REINDEX")
        
        # Vacuum database to reclaim space
        cursor.execute("VACUUM")
        
        conn.commit()
        logger.info("Database optimization completed")
        
    except sqlite3.Error as e:
        logger.error(f"Database optimization error: {str(e)}")
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
            WHERE name IN ('news', 'teams', 'events', 'ewc_info', 'games', 'matches', 'transfers', 
                           'prize_distribution', 'global_matches', 'ewc_teams_players', 'team_information',
                           'player_information', 'group_matches')
        """)
        conn.commit()
        logger.debug("Reset SQLite sequence for all tables")
    except sqlite3.Error as e:
        logger.error(f"Failed to reset SQLite sequence: {str(e)}")
        raise
    finally:
        conn.close()

def get_database_stats():
    """Get database statistics for monitoring"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        stats = {}
        
        # Get table counts
        tables = ['news', 'teams', 'events', 'games', 'matches', 'transfers', 
                 'global_matches', 'ewc_teams_players', 'player_information', 
                 'team_information', 'group_matches', 'prize_distribution', 'ewc_info']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except sqlite3.Error:
                stats[table] = 0
        
        # Get database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        stats['database_size_bytes'] = db_size
        stats['database_size_mb'] = round(db_size / (1024 * 1024), 2)
        
        return stats
        
    except sqlite3.Error as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {}
    finally:
        conn.close()