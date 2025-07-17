from app.db import get_connection

def init_game_teams_db():
    """Create the game_teams table and FTS5 table with triggers."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create game_teams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL,
            team_logo_url TEXT,
            game_name TEXT NOT NULL,
            game_url TEXT,
            logo_mode TEXT,
            logo_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create FTS5 virtual table
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS game_teams_fts USING fts5(
            team_name, game_name, logo_mode,
            content=game_teams, content_rowid=id
        )
    ''')
    
    # Create triggers to keep FTS table in sync
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS game_teams_ai AFTER INSERT ON game_teams BEGIN
            INSERT INTO game_teams_fts(rowid, team_name, game_name, logo_mode)
            VALUES (new.id, new.team_name, new.game_name, new.logo_mode);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS game_teams_ad AFTER DELETE ON game_teams BEGIN
            INSERT INTO game_teams_fts(game_teams_fts, rowid, team_name, game_name, logo_mode)
            VALUES ('delete', old.id, old.team_name, old.game_name, old.logo_mode);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS game_teams_au AFTER UPDATE ON game_teams BEGIN
            INSERT INTO game_teams_fts(game_teams_fts, rowid, team_name, game_name, logo_mode)
            VALUES ('delete', old.id, old.team_name, old.game_name, old.logo_mode);
            INSERT INTO game_teams_fts(rowid, team_name, game_name, logo_mode)
            VALUES (new.id, new.team_name, new.game_name, new.logo_mode);
        END
    ''')
    
    conn.commit()
    conn.close()