# app/__init__.py

import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
from flasgger import Swagger

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, static_folder='static')

    # Enable CORS
    CORS(app)

    # Initialize database
    from .db import init_db
    from .game_teams_init_db import init_game_teams_db
    init_db()
    init_game_teams_db()

    # Initialize Swagger
    swagger = Swagger(app)

    # Register blueprints with unique import names
    from .routes.news import news_bp
    from .routes.games import games_bp
    from .routes.prizes import prize_bp
    from .routes.info import info_bp
    from .routes.player_transfers import player_transfers_bp
    from .routes.ewc_rank_route import ewc_rank_bp
    from .routes.ewc_teams_players import ewc_teams_players_bp
    from .routes.team_information import team_information_bp
    from .routes.player_information import player_information_bp
    from .routes.search import search_bp
    from .routes.search_extended import search_extended_bp
    from .routes.game_matches import game_matches_bp
    from .routes.game_teams import new_teams_bp
    from app.routes.matches_mohamed import matches_bp
    from app.routes.ewc_weeks import weeks_bp
    from auto_live_player_info.fetch_player_info_script import live_player_info_automatic_bp


    # Register all blueprints
    app.register_blueprint(news_bp, url_prefix="/api")
    app.register_blueprint(prize_bp, url_prefix="/api")
    app.register_blueprint(games_bp, url_prefix="/api")
    app.register_blueprint(info_bp, url_prefix="/api")
    app.register_blueprint(player_transfers_bp, url_prefix="/api")
    app.register_blueprint(ewc_rank_bp, url_prefix="/api")
    app.register_blueprint(ewc_teams_players_bp, url_prefix="/api")
    app.register_blueprint(team_information_bp, url_prefix="/api")
    app.register_blueprint(player_information_bp, url_prefix="/api")
    app.register_blueprint(search_bp, url_prefix="/api")
    app.register_blueprint(search_extended_bp, url_prefix="/api/extended")
    app.register_blueprint(game_matches_bp, url_prefix="/api")
    app.register_blueprint(new_teams_bp, url_prefix="/api")
    app.register_blueprint(matches_bp, url_prefix="/api")
    app.register_blueprint(weeks_bp, url_prefix="/api")
    app.register_blueprint(live_player_info_automatic_bp, url_prefix="/api")


    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        import os
        upload_dir = os.path.join(app.root_path, '..', 'static', 'uploads')
        return send_from_directory(upload_dir, filename)

    return app