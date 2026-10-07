"""WSGI entry point: ``gunicorn wsgi:app`` or ``waitress-serve wsgi:app``."""
from __future__ import annotations

import os

from app import create_app

app = create_app(os.environ.get("FLASK_CONFIG", "production"))
