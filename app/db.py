import sqlite3

def get_connection():
    conn = sqlite3.connect("news.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
   # Create prize_distribution table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prize_distribution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place TEXT,
            place_logo TEXT,
            prize TEXT,
            participants TEXT,
            logo_team TEXT
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

    # Create games table (if not already added)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            genre TEXT,
            platform TEXT,
            release_date TEXT,
            description TEXT,
            logo TEXT
        )
    ''')
    # Create teams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            logo_url TEXT
        )
    ''')

    # Create events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        link TEXT
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
            score TEXT
        )
    ''') 
    conn.commit()
    conn.close()
