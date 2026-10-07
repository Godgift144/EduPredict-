"""Flask application factory.

Usage::

    from app import create_app
    app = create_app()
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

from .config import get_config
from .extensions import csrf, db, login_manager


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app.logger.setLevel(level)


def register_cli(app: Flask) -> None:
    """Flask CLI commands: ``flask --app app init-db`` / ``seed`` / ``train``."""

    @app.cli.command("init-db")
    def init_db_command():
        """Create all database tables."""
        db.create_all()
        print("Database tables created.")

    @app.cli.command("train")
    def train_command():
        """Train and persist the prediction model."""
        from .ml.train import train_experiment

        summary = train_experiment(
            app.config["TRAINING_DATA_PATH"],
            app.config["ARTIFACTS_FOLDER"],
            verbose=True,
        )
        print(
            f"Trained {summary['best_model']} "
            f"(accuracy={summary['best_metrics']['accuracy']:.3f})"
        )

    @app.cli.command("seed")
    def seed_command():
        """Seed demo users, students and predictions."""
        from .seed import seed_database

        stats = seed_database()
        print(f"Seeded: {stats}")


def create_app(config_name: str | None = None) -> Flask:
    """Build and return the configured Flask application."""
    # Load .env if present (no-op when missing).
    from dotenv import load_dotenv

    load_dotenv()

    app = Flask(__name__, instance_relative_config=False)
    resolved = (config_name or os.environ.get("FLASK_CONFIG", "development")).lower()
    app.config.from_object(get_config(resolved))
    app.config["APP_VERSION"] = "1.0.0"

    # Refuse to boot an insecure production instance.
    if resolved == "production" and len(os.environ.get("SECRET_KEY", "")) < 16:
        raise RuntimeError(
            "SECRET_KEY (at least 16 characters) must be provided via the "
            "environment when FLASK_CONFIG=production."
        )

    # Ensure project directories exist.
    for key in ("UPLOAD_FOLDER", "RAW_DATA_FOLDER", "ARTIFACTS_FOLDER", "PLOTS_FOLDER"):
        os.makedirs(app.config[key], exist_ok=True)

    _configure_logging(app)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        from .models import User

        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):  # pragma: no cover
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify(error="Authentication required"), 401
        from flask import redirect, url_for

        return redirect(url_for("auth.login", next=request.path))

    # Blueprints
    from .api import api_bp
    from .auth import auth_bp
    from .main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Errors
    from .errors import register_error_handlers

    register_error_handlers(app)

    # CLI
    register_cli(app)

    # Template globals
    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.now(timezone.utc).year,
            "app_version": app.config["APP_VERSION"],
        }

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if request.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    # Create tables on boot (idempotent; fine for SQLite/MySQL prototypes).
    with app.app_context():
        try:
            db.create_all()
        except Exception as exc:  # pragma: no cover - surfaced in logs
            app.logger.error("Could not create database tables: %s", exc)

    return app
