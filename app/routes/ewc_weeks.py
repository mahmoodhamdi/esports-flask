from flask import Flask, jsonify, request, Blueprint
import sqlite3
from app.db import get_connection
from urllib.parse import urlparse, unquote
 
weeks_bp = Blueprint('weeks', __name__)

@weeks_bp.route('/weeks', methods=['GET'])
def get_weeks():
    """
    GET /api/weeks - جلب كل الأسابيع والألعاب الخاصة بها
    Response format:
    {
        'current_week': "Week 1",
        'weeks': [
            {
                'name': 'Week 1',
                "games": [
            "Real Madrid",
            "Barcelona",
            "Liverpool",
            "Manchester City"
        ] 
            }
        ]
    }
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # جلب current_week
        cursor.execute("SELECT value FROM settings_in_week WHERE key = 'current_week'")
        current_week_row = cursor.fetchone()
        current_week = current_week_row["value"] if current_week_row else "Week 1"

        # جلب كل الأسابيع والألعاب
        cursor.execute("SELECT * FROM weeks ORDER BY id")
        weeks_rows = cursor.fetchall()

        weeks = []
        for week in weeks_rows:
            cursor.execute("SELECT game_name FROM games_in_week WHERE week_id = ? ORDER BY id", (week["id"],))
            games_rows = cursor.fetchall()
            games = [row["game_name"] for row in games_rows]
            weeks.append({
                "name": week["name"],
                "games": games
            })

        conn.close()

        return jsonify({
            "current_week": current_week,
            "weeks": weeks
        }), 200

    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@weeks_bp.route('/weeks', methods=['POST'])
def add_week():
    """
    POST /api/weeks - إضافة أسبوع جديد
    Request body:
    {
        "name": "Week 3",
        "games": [
            "Real Madrid",
            "Barcelona",
            "Liverpool",
            "Manchester City"
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        name = data.get("name")
        games = data.get("games", [])

        # التحقق من صحة البيانات
        if not name:
            return jsonify({"error": "Week name is required"}), 400
            
        if not isinstance(games, list):
            return jsonify({"error": "Games must be a list"}), 400

        # التحقق من صحة تنسيق الألعاب
        for i, game in enumerate(games):
            if not isinstance(game, str) or not game.strip():
                return jsonify({"error": f"Game {i+1} must be a non-empty string"}), 400

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # إضافة الأسبوع الجديد
            cursor.execute("INSERT INTO weeks (name) VALUES (?)", (name.strip(),))
            week_id = cursor.lastrowid

            # إضافة الألعاب للأسبوع الجديد
            for game in games:
                cursor.execute(
                    "INSERT INTO games_in_week (week_id, game_name) VALUES (?, ?)", 
                    (week_id, game.strip())
                )

            conn.commit()
            return jsonify({
                "message": "Week added successfully",
                "week_id": week_id,
                "name": name,
                "games_count": len(games)
            }), 201

        except sqlite3.IntegrityError:
            return jsonify({"error": "Week name already exists"}), 409
        finally:
            conn.close()

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@weeks_bp.route('/current-week', methods=['PUT'])
def update_current_week():
    """
    PUT /api/current-week - تحديث الأسبوع الحالي
    Request body:
    {
        "current_week": "Week 2"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        new_week = data.get("current_week")
        
        if not new_week:
            return jsonify({"error": "current_week is required"}), 400
            
        if not isinstance(new_week, str) or not new_week.strip():
            return jsonify({"error": "current_week must be a non-empty string"}), 400

        conn = get_connection()
        cursor = conn.cursor()

        # التحقق من وجود الأسبوع في قاعدة البيانات
        cursor.execute("SELECT id FROM weeks WHERE name = ?", (new_week.strip(),))
        week_exists = cursor.fetchone()
        
        if not week_exists:
            conn.close()
            return jsonify({"error": "Week does not exist"}), 404

        # تحديث current_week
        cursor.execute("UPDATE settings_in_week SET value = ? WHERE key = 'current_week'", (new_week.strip(),))
        
        # إذا لم يكن هناك صف للـ current_week، قم بإنشائه
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO settings_in_week (key, value) VALUES ('current_week', ?)", (new_week.strip(),))
        
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Current week updated successfully",
            "current_week": new_week.strip()
        }), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@weeks_bp.route('/weeks/<week_name>', methods=['GET'])
def get_week_by_name(week_name):
    """
    GET /api/weeks/<week_name> - جلب أسبوع محدد بالاسم
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM weeks WHERE name = ?", (week_name,))
        week = cursor.fetchone()
        
        if not week:
            return jsonify({"error": "Week not found"}), 404

        cursor.execute("SELECT game_name FROM games_in_week WHERE week_id = ? ORDER BY id", (week["id"],))
        games_rows = cursor.fetchall()
        games = [row["game_name"] for row in games_rows]

        conn.close()

        return jsonify({
            "name": week["name"],
            "games": games
        }), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@weeks_bp.route('/weeks/<week_name>', methods=['DELETE'])
def delete_week(week_name):
    """
    DELETE /api/weeks/<week_name> - حذف أسبوع محدد
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM weeks WHERE name = ?", (week_name,))
        week = cursor.fetchone()
        
        if not week:
            return jsonify({"error": "Week not found"}), 404

        # حذف الألعاب المرتبطة بالأسبوع أولاً
        cursor.execute("DELETE FROM games_in_week WHERE week_id = ?", (week["id"],))
        
        # ثم حذف الأسبوع
        cursor.execute("DELETE FROM weeks WHERE id = ?", (week["id"],))
        
        conn.commit()
        conn.close()

        return jsonify({"message": f"Week '{week_name}' deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@weeks_bp.route('/weeks/<week_name>/_in_week', methods=['POST'])
def add_game_to_week(week_name):
    """
    POST /api/weeks/<week_name>/games - إضافة لعبة جديدة لأسبوع محدد
    Request body:
    {
        "game_name": "Real Madrid"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        game_name = data.get("game_name")
        
        if not game_name:
            return jsonify({"error": "game_name is required"}), 400
            
        if not isinstance(game_name, str) or not game_name.strip():
            return jsonify({"error": "game_name must be a non-empty string"}), 400

        conn = get_connection()
        cursor = conn.cursor()

        # التحقق من وجود الأسبوع
        cursor.execute("SELECT id FROM weeks WHERE name = ?", (week_name,))
        week = cursor.fetchone()
        
        if not week:
            conn.close()
            return jsonify({"error": "Week not found"}), 404

        # إضافة اللعبة الجديدة
        cursor.execute(
            "INSERT INTO games_in_week (week_id, game_name) VALUES (?, ?)", 
            (week["id"], game_name.strip())
        )
        
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Game added successfully",
            "week_name": week_name,
            "game_name": game_name.strip()
        }), 201

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500