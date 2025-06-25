import logging
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
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
    from .routes.matches import matches_bp as group_matches_bp   # Renamed
    
    # Register all blueprints
    app.register_blueprint(news_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(prize_bp, url_prefix="/api")
    app.register_blueprint(games_bp, url_prefix="/api")
    app.register_blueprint(info_bp, url_prefix="/api")
    app.register_blueprint(teams_bp, url_prefix="/api")
    app.register_blueprint(events_bp, url_prefix="/api")
    app.register_blueprint(ewc_matches_bp, url_prefix="/api")      # EWC matches
    app.register_blueprint(transfers_bp, url_prefix="/api")
    app.register_blueprint(group_matches_bp, url_prefix="/api/matches/group_matches")  # Group matches

    return app