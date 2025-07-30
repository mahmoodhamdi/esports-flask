from app.db import get_connection, generate_match_uid

def update_missing_uids():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, game, team1, team2, match_time, details_link FROM matches
        WHERE uid IS NULL OR uid = ''
    ''')
    rows = cursor.fetchall()

    print(f"🔍 Found {len(rows)} rows missing uid...")

    for row in rows:
        match_id = row["id"]
        game = row["game"] or ''
        team1 = row["team1"] or ''
        team2 = row["team2"] or ''
        match_time = row["match_time"] or ''
        details_link = row["details_link"] or ''

        uid = generate_match_uid(game, team1, team2, match_time, details_link)

        # 👇 تحقق من التكرار
        cursor.execute('SELECT id FROM matches WHERE uid = ?', (uid,))
        existing = cursor.fetchone()
        if existing and existing["id"] != match_id:
            print(f"⚠️ Skipping match ID {match_id} due to duplicate UID")
            continue

        cursor.execute('''
            UPDATE matches SET uid = ? WHERE id = ?
        ''', (uid, match_id))

    conn.commit()
    conn.close()
    print("✅ All missing UIDs have been updated.")

if __name__ == "__main__":
    update_missing_uids()
