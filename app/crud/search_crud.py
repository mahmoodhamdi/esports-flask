import json
from app.db import get_connection

MAX_RESULTS_PER_TABLE = 1000

SEARCH_TYPES = {
    "news": "news",
    "teams": "teams",
    "events": "events",
    "games": "games",
    "matches": "matches",
    "players": "player_information",
}

SEARCH_FIELDS = {
    "news": ["title", "description"],
    "teams": ["team_name"],
    "events": ["name"],
    "games": ["game_name", "description"],
    "matches": ["team1_name", "team2_name"],
    "players": ["Name", "Player_Information.Romanized Name"],
}

FILTER_FIELDS = {
    "news": ["writer"],
    "players": ["Nationality"],
}

def search_table(search_type, query, page, per_page, filter_field=None, filter_value=None, for_global_search=False):
    table_name = SEARCH_TYPES.get(search_type)
    if not table_name:
        return [], 0
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if table_name not in ["player_information", "team_information"]:
            # SQL table
            search_fields = SEARCH_FIELDS.get(search_type, [])
            if not search_fields:
                return [], 0
            where_clauses = [f"{field} LIKE ?" for field in search_fields]
            sql = f"SELECT * FROM {table_name} WHERE " + " OR ".join(where_clauses)
            params = [f"%{query}%"] * len(search_fields)
            if filter_field and filter_value and filter_field in FILTER_FIELDS.get(search_type, []):
                sql += f" AND {filter_field} = ?"
                params.append(filter_value)
            
            # Get total count
            count_sql = f"SELECT COUNT(*) FROM {table_name} WHERE " + " OR ".join(where_clauses)
            count_params = params.copy()
            if filter_field and filter_value and filter_field in FILTER_FIELDS.get(search_type, []):
                count_sql += f" AND {filter_field} = ?"
            cursor.execute(count_sql, count_params)
            total = cursor.fetchone()[0]
            
            if not for_global_search:
                offset = (page - 1) * per_page
                sql += " LIMIT ? OFFSET ?"
                params.extend([per_page, offset])
            else:
                sql += " LIMIT ?"
                params.append(MAX_RESULTS_PER_TABLE)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows], total
        elif table_name == "player_information":
            # JSON table
            cursor.execute("SELECT data FROM player_information")
            rows = cursor.fetchall()
            players = [json.loads(row['data']) for row in rows]
            if query:
                query = query.lower()
                players = [
                    p for p in players
                    if query in p.get("Name", "").lower() or
                       query in p.get("Player_Information", {}).get("Romanized Name", "").lower()
                ]
            if filter_field == "Nationality" and filter_value:
                players = [p for p in players if p.get("Player_Information", {}).get("Nationality", {}).get("text") == filter_value]
            
            total = len(players)
            if not for_global_search:
                start = (page - 1) * per_page
                end = start + per_page
                paginated_players = players[start:end]
            else:
                paginated_players = players[:MAX_RESULTS_PER_TABLE]
            return paginated_players, total
        else:
            return [], 0
    finally:
        conn.close()

def global_search(query, page, per_page, filter_field=None, filter_value=None):
    results_by_type = {search_type: [] for search_type in SEARCH_TYPES}
    total = 0
    
    for search_type in SEARCH_TYPES:
        results, table_total = search_table(search_type, query, 1, per_page, filter_field, filter_value, for_global_search=True)
        results_by_type[search_type] = results
        total += table_total
    
    # Apply global pagination
    all_results = []
    for search_type, items in results_by_type.items():
        all_results.extend(items)
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_all_results = all_results[start:end]
    
    # Rebuild results_by_type with paginated results
    paginated_results_by_type = {search_type: [] for search_type in SEARCH_TYPES}
    for item in paginated_all_results:
        for search_type in SEARCH_TYPES:
            if item in results_by_type[search_type]:
                paginated_results_by_type[search_type].append(item)
                break
    
    return paginated_results_by_type, total