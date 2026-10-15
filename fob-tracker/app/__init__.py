import os
from pathlib import Path

from flask import Flask
from dotenv import load_dotenv


def create_app(test_config: dict | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__, instance_relative_config=False)

    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me"),
        ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME", "manager"),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "change-me"),
        DATABASE_PATH=os.environ.get("DATABASE_PATH", "./fob-tracker.db"),
        API_CORS_ORIGINS=os.environ.get("API_CORS_ORIGINS", "*"),
        BRAND_NAME=os.environ.get("BRAND_NAME", "Fob Tracker"),
        BRAND_COLOR=os.environ.get("BRAND_COLOR", "#1E8A8A"),
    )
    if test_config:
        app.config.update(test_config)

    from . import db

    db.init_app(app)

    from .routes.scan import bp as scan_bp
    from .routes.admin import bp as admin_bp
    from .routes.export import bp as export_bp
    from .routes.api import bp as api_bp

    app.register_blueprint(scan_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(export_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    @app.after_request
    def apply_cors(response):
        if response.headers.get("X-Fob-Api") == "1":
            origin = app.config["API_CORS_ORIGINS"]
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "X-API-Key, Content-Type"
        return response

    @app.context_processor
    def inject_branding():
        return {
            "brand_name": app.config["BRAND_NAME"],
            "brand_color": app.config["BRAND_COLOR"],
        }

    return app
