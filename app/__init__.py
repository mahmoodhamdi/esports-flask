from flask import Flask
from flasgger import Swagger
from .db import init_db
from .routes.games import games_bp
from .routes.prizes import prize_bp
from .routes.info import info_bp
from app.routes.ewc_teams import teams_bp
from app.routes.ewc_events import events_bp
from app.routes.ewc_matches import matches_bp
from app.routes.ewc_transfers import transfers_bp
def create_app():
    app = Flask(__name__)
    init_db()
    Swagger(app)

    app.register_blueprint(prize_bp, url_prefix="/api")
    app.register_blueprint(games_bp, url_prefix="/api")
    app.register_blueprint(info_bp, url_prefix="/api")
    app.register_blueprint(teams_bp, url_prefix="/api")
    app.register_blueprint(events_bp, url_prefix="/api")
    app.register_blueprint(matches_bp, url_prefix="/api")
    app.register_blueprint(transfers_bp, url_prefix="/api")

    return app
