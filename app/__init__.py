from flask import Flask
from flasgger import Swagger
from .db import init_db
from .routes.games import games_bp
from .routes.prizes import prize_bp
from .routes.info import info_bp
def create_app():
    app = Flask(__name__)
    init_db()

    # Add Swagger docs
    Swagger(app)
    app.register_blueprint(prize_bp, url_prefix="/api")
    app.register_blueprint(games_bp, url_prefix="/api")
    app.register_blueprint(info_bp, url_prefix="/api")
    return app
