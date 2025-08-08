from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request, jsonify
from dataclasses import dataclass
from typing import List, Optional
import json
import sqlite3
import pytz
from app.db import get_connection
from app.matches_dashborad.match_model import MatchModel


def validate_match_data(match_data: dict) -> tuple[bool, str]:
    """
    التحقق من صحة بيانات المباراة
    Returns: (is_valid, reason)
    """
    team1 = match_data.get("team1", "N/A")
    team2 = match_data.get("team2", "N/A")
    
    # الشرط الأساسي: على الأقل واحد من الفريقين معروف
    if team1 == "N/A" and team2 == "N/A":
        return False, "الفريقان غير معروفان"
    
    return True, "صحيح"

def determine_match_status(original_status: str, score: str) -> str:
    """
    تحديد حالة المباراة الفعلية بناءً على status و score
    
    Rules:
    - Upcoming + empty score = "Upcoming" (مباراة قادمة)
    - Upcoming + score = "live" (مباراة مباشرة)
    - Completed + score = "Completed" (مباراة منتهية)
    """
    if not score or score.strip() == "":
        # لو مافيش سكور، يبقى المباراة لسه جاية
        return "Upcoming"
    
    # لو فيه سكور
    if original_status == "Completed":
        return "Completed"  # مباراة منتهية
    elif original_status == "Upcoming":
        return "live"  # مباراة مباشرة (كان مقرر تبدأ ودلوقتي فيها سكور)
    else:
        return original_status  # أي حالة تانية زي live مثلاً

def save_live_matches_to_db(game: str, matches: list):
    """
    دالة مخصصة لحفظ المباريات المُرسلة مباشرة من API
    مع تحديث حالة المباراة بناءً على Status و Score
    """
    from app.matches_mohamed import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # حذف جميع المباريات للعبة المحددة (مش بس live)
    cursor.execute("DELETE FROM matches WHERE game = ?", (game,))
    
    saved_matches = 0
    skipped_matches = 0
    status_summary = {"Upcoming": 0, "live": 0, "Completed": 0}
    
    for match in matches:
        # التحقق من صحة البيانات
        match_dict = {
            "team1": match.team1,
            "team2": match.team2
        }
        
        is_valid, reason = validate_match_data(match_dict)
        
        if not is_valid:
            skipped_matches += 1
            print(f"❌ تم تخطي مباراة: {reason} - {match.team1} vs {match.team2}")
            continue
        
        # تحديد حالة المباراة الفعلية بناءً على status و score
        actual_status = determine_match_status(match.status, match.score)
        status_summary[actual_status] += 1
        
        print(f"🔄 تحديث حالة المباراة: {match.team1} vs {match.team2}")
        print(f"   الحالة الأصلية: {match.status}, السكور: '{match.score}'")
        print(f"   الحالة المُحدّثة: {actual_status}")
        
        # حفظ المباراة مع الحالة المُحدّثة
        cursor.execute(
            '''
            INSERT INTO matches (
                game, status, tournament, tournament_link, tournament_icon,
                team1, team1_url, logo1_light, logo1_dark,
                team2, team2_url, logo2_light, logo2_dark,
                score, match_time, format, stream_links, details_link, match_group
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match.game, actual_status, match.tournament,  # استخدام actual_status بدلاً من match.status
                match.tournament_link, match.tournament_icon,
                match.team1, match.team1_url, match.logo1_light, match.logo1_dark,
                match.team2, match.team2_url, match.logo2_light, match.logo2_dark,
                match.score, match.match_time, match.format,
                json.dumps(match.stream_links) if match.stream_links else json.dumps([]),
                match.details_link, match.match_group
            ))
        saved_matches += 1
    
    print(f"✅ حُفظت {saved_matches} مباراة، تُخطيت {skipped_matches} مباراة")
    print(f"📊 توزيع المباريات: {status_summary}")
    
    conn.commit()
    conn.close()
    
    return {
        'saved': saved_matches,
        'skipped': skipped_matches,
        'status_distribution': status_summary
    }

def get_matches_by_filters(games=[], tournaments=[], live=False, page=1, per_page=10):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM matches WHERE 1=1"
    params = []

    if games:
        query += f" AND game IN ({','.join(['?'] * len(games))})"
        params.extend(games)

    if tournaments:
        query += f" AND tournament IN ({','.join(['?'] * len(tournaments))})"
        params.extend(tournaments)

    if live:
        query += " AND status = 'Not Started'"

    query += " ORDER BY id ASC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    cursor.execute(query, params)
    matches = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM matches WHERE 1=1", ())
    total = cursor.fetchone()[0]

    keys = [column[0] for column in cursor.description]
    result = [dict(zip(keys, row)) for row in matches]

    conn.close()
    return result, total


def get_matches_from_db(game: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE game = ?", (game, ))
    rows = cursor.fetchall()
    conn.close()

    result = {}
    for row in rows:
        result.setdefault(row["status"], {}).setdefault(row["tournament"], {"matches": []})["matches"].append({
            "team1": row["team1"],
            "team2": row["team2"],
            "score": row["score"],
            "match_time": row["match_time"],
            "format": row["format"],
            "stream_link": row["stream_link"],
            "group": row["match_group"]
        })

    return result


def parse_match_date(match_time_str, timezone_str="UTC"):
    try:
        if not match_time_str or match_time_str == "N/A":
            return None

        date_part, time_part = match_time_str.split(" - ")
        dt = datetime.strptime(f"{date_part} {time_part}", "%B %d, %Y %H:%M")
        dt = pytz.utc.localize(dt)
        local_tz = pytz.timezone(timezone_str)
        local_dt = dt.astimezone(local_tz)
        return local_dt
    except Exception as e:
        return None
# Helper Function to Normalize Tournament Names
def normalize_tournament_name(tournament_name: str) -> str:
    TOURNAMENT_NAME_MAP = {
        "OWCS Midseason": "Overwatch Champions",
        "FCP": "FC Pro 25 World Championship",
    }
    for keyword, replacement in TOURNAMENT_NAME_MAP.items():
        if keyword in tournament_name:
            return replacement
    return tournament_name

def get_matches_paginated(games: list = [],
                          tournaments: list = [],
                          live: bool = False,
                          day: str = None,
                          page: int = 1,
                          per_page: int = 10,
                          timezone: str = "UTC"):
    conn = get_connection()
    cursor = conn.cursor()

    # Build WHERE conditions
    where_clauses = []
    params = []

    if games:
        where_clauses.append(f"game IN ({','.join(['?'] * len(games))})")
        params.extend(games)

    if tournaments:
        where_clauses.append(
            f"tournament IN ({','.join(['?'] * len(tournaments))})")
        params.extend(tournaments)

    if live:
        where_clauses.append("status = 'Not Started'")

    if day:
        try:
            filter_date = datetime.strptime(day, "%Y-%m-%d").date()
            where_clauses.append(
                "match_time != 'N/A' AND match_time IS NOT NULL")
        except ValueError:
            pass

    where_sql = " AND ".join(where_clauses)
    if where_sql:
        where_sql = "WHERE " + where_sql

    cursor.execute(
        f"""
        SELECT *
        FROM matches
        {where_sql}
        ORDER BY tournament, match_time
        """, params)

    all_matches = cursor.fetchall()
    keys = [column[0] for column in cursor.description]
    matches_data = [dict(zip(keys, row)) for row in all_matches]

    # تحويل الوقت إلى التوقيت المحلي إذا كان live=False
    if not live and timezone:
        for match in matches_data:
            if match['match_time'] and match['match_time'] != 'N/A':
                try:
                    # تحويل الوقت من UTC إلى التوقيت المحلي
                    dt_utc = datetime.fromisoformat(match['match_time'])
                    local_tz = ZoneInfo(timezone)
                    local_dt = dt_utc.astimezone(local_tz)
                    match['match_time'] = local_dt.isoformat()
                except ValueError:
                    match[
                        'match_time'] = None  # في حالة وجود خطأ في تحويل الوقت

    # Apply day filter in Python if specified
    if day:
        try:
            filter_date = datetime.strptime(day, "%Y-%m-%d").date()
            filtered_matches = []
            for match in matches_data:
                if match['match_time'] and match['match_time'] != 'N/A':
                    match_dt = datetime.fromisoformat(
                        match['match_time']).date()
                    if match_dt == filter_date:
                        filtered_matches.append(match)
                else:
                    continue
            matches_data = filtered_matches
        except ValueError:
            pass
    # Group matches by tournament
    tournaments_map = {}
    for match in matches_data:
        match['tournament'] = normalize_tournament_name(match['tournament'])
        tournament_name = match['tournament']
        if tournament_name not in tournaments_map:
            tournaments_map[tournament_name] = {
                "tournament_name": tournament_name,
                "tournament_icon": match.get("tournament_icon", ""),
                "tournament_link": match.get("tournament_link", ""),
                "games": []
            }

        game_entry = next((g for g in tournaments_map[tournament_name]["games"]
                           if g["game"] == match["game"]), None)
        if not game_entry:
            game_entry = {"game": match["game"], "matches": []}
            tournaments_map[tournament_name]["games"].append(game_entry)

        game_entry["matches"].append({
            "team1":
            match["team1"],
            "team1_url":
            match.get("team1_url"),
            "logo1_light":
            match["logo1_light"],
            "logo1_dark":
            match["logo1_dark"],
            "team2":
            match["team2"],
            "team2_url":
            match.get("team2_url"),
            "logo2_light":
            match["logo2_light"],
            "logo2_dark":
            match["logo2_dark"],
            "score":
            match["score"],
            "match_time":
            match["match_time"],
            "format":
            match["format"],
            "stream_link":
            json.loads(match["stream_links"])
            if match.get("stream_links") else [],
            "details_link":
            match.get("details_link"),
            "group":
            match["match_group"],
            "status":
            match["status"]
        })

    # Apply pagination to tournaments
    total_tournaments = len(tournaments_map)
    tournament_list = list(tournaments_map.values())

    # Sort tournaments
    priority_keywords = [
        'FC',
        'FCP',
        'MSC',
        'Hok World Cup',
        'EWC',
        'OWCS',
        'OWCS Season',
        'OWCS Midseason',
        'Honor of Kings World Cup',
        'Esports World Cup 2025',
        'EWC 2025',
        'Esports World Cup',
        'Esports World',
        'Esports',
        'World Cup',
        'PUBG Mobile World Cup',
        'Overwatch',
    ]

    def get_priority_index(name: str) -> int:
        name_lower = name.lower()
        for i, keyword in enumerate(priority_keywords):
            if keyword.lower() in name_lower:
                return i
        return len(priority_keywords) + 1  # non-priority

    # فلترة البطولات ذات الأولوية فقط
    tournament_list = [
        t for t in tournament_list
        if any(keyword.lower() in t["tournament_name"].lower()
               for keyword in priority_keywords)
    ]

    # ترتيب البطولات
    tournament_list.sort(key=lambda t: (get_priority_index(t[
        "tournament_name"]), t["tournament_name"].lower()))

    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_tournaments = tournament_list[start_idx:end_idx]

    # Sort matches within each tournament
    for tournament in paginated_tournaments:
        for game_entry in tournament["games"]:
            game_entry["matches"].sort(key=lambda m: m["match_time"])
        tournament["games"] = sorted(tournament["games"],
                                     key=lambda g: g["game"])

    conn.close()

    return {
        "page": page,
        "per_page": per_page,
        "total": len(tournament_list),
        "tournaments": paginated_tournaments
    }