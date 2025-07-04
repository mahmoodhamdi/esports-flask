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
    init_db()

    # Initialize Swagger
    swagger = Swagger(app)

    # Register blueprints with unique import names
    from .routes.news import news_bp
    from .routes.admin import admin_bp
    from .routes.games import games_bp
    from .routes.prizes import prize_bp
    from .routes.info import info_bp
    from .routes.ewc_teams import teams_bp
    from .routes.ewc_events import events_bp
    from .routes.ewc_matches import matches_bp as ewc_matches_bp  # Renamed
    from .routes.ewc_transfers import transfers_bp
    from .routes.global_matches import global_matches_bp
    from .routes.player_transfers import player_transfers_bp
    from .routes.ewc_rank_route import ewc_rank_bp
    from .routes.ewc_teams_players import ewc_teams_players_bp
    from .routes.team_information import team_information_bp
    from .routes.player_information import player_information_bp
    from .routes.search import search_bp
    from .routes.search_extended import search_extended_bp

    # Register all blueprints
    app.register_blueprint(news_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(prize_bp, url_prefix="/api")
    app.register_blueprint(games_bp, url_prefix="/api")
    app.register_blueprint(info_bp, url_prefix="/api")
    app.register_blueprint(teams_bp, url_prefix="/api")
    app.register_blueprint(events_bp, url_prefix="/api")
    app.register_blueprint(ewc_matches_bp, url_prefix="/api")  # EWC matches
    app.register_blueprint(transfers_bp, url_prefix="/api")
    app.register_blueprint(global_matches_bp,
                           url_prefix="/api")  # Global matches
    app.register_blueprint(player_transfers_bp,
                           url_prefix="/api")  # Player transfers
    app.register_blueprint(ewc_rank_bp, url_prefix="/api")
    app.register_blueprint(ewc_teams_players_bp, url_prefix="/api")
    app.register_blueprint(team_information_bp, url_prefix="/api")
    app.register_blueprint(player_information_bp, url_prefix="/api")
    app.register_blueprint(search_bp, url_prefix="/api")
    app.register_blueprint(search_extended_bp, url_prefix="/api/extended")

    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        import os
        upload_dir = os.path.join(app.root_path, '..', 'static', 'uploads')
        return send_from_directory(upload_dir, filename)

    return app
