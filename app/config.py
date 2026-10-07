"""Application configuration.

Configuration is driven by environment variables so the same code base can run
in development, testing and production (see .env.example).
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
RAW_DATA_DIR = DATA_DIR / "raw"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
PLOTS_DIR = ARTIFACTS_DIR / "plots"
MODEL_PATH = ARTIFACTS_DIR / "model.joblib"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"
TRAINING_DATA_PATH = RAW_DATA_DIR / "student_records.csv"


def _default_db_url() -> str:
    """SQLite URL stored inside the project ``data`` directory."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"


class Config:
    """Base configuration shared by all environments."""

    # ------------------------------------------------------------------ #
    # Core Flask
    # ------------------------------------------------------------------ #
    SECRET_KEY = os.environ.get("SECRET_KEY") or "insecure-dev-key-change-me"
    FLASK_ENV = os.environ.get("FLASK_CONFIG", "development")

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or _default_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    # ------------------------------------------------------------------ #
    # Security / sessions
    # ------------------------------------------------------------------ #
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = None
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", "5")) * 1024 * 1024

    # ------------------------------------------------------------------ #
    # Project paths
    # ------------------------------------------------------------------ #
    UPLOAD_FOLDER = str(UPLOAD_DIR)
    RAW_DATA_FOLDER = str(RAW_DATA_DIR)
    ARTIFACTS_FOLDER = str(ARTIFACTS_DIR)
    PLOTS_FOLDER = str(PLOTS_DIR)
    MODEL_PATH = str(ARTIFACTS_DIR / "model.joblib")
    METRICS_PATH = str(ARTIFACTS_DIR / "metrics.json")
    TRAINING_DATA_PATH = str(RAW_DATA_DIR / "student_records.csv")
    UPLOAD_TEMPLATE_PATH = str(RAW_DATA_DIR / "student_records_template.csv")

    # ------------------------------------------------------------------ #
    # Modelling
    # ------------------------------------------------------------------ #
    RANDOM_SEED = 42
    TEST_SIZE = 0.2
    # Accuracy below which the model is considered unfit for deployment.
    MIN_ACCEPTED_ACCURACY = 0.70

    # Pagination
    STUDENTS_PER_PAGE = 15


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    # Tests get their own throwaway database.
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {}


class ProductionConfig(Config):
    DEBUG = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    name = (name or os.environ.get("FLASK_CONFIG", "development")).lower()
    return CONFIG_MAP.get(name, DevelopmentConfig)
