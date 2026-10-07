"""Application entry point.

Development:   python run.py
Production:    python run.py --prod           (Waitress WSGI server)
               FLASK_CONFIG=production SECRET_KEY=... python wsgi.py (Gunicorn)
"""
from __future__ import annotations

import argparse
import os

from app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the EduRisk Predictor server.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--prod", action="store_true", help="Serve with Waitress (production WSGI)")
    args = parser.parse_args()

    config_name = os.environ.get("FLASK_CONFIG", "production" if args.prod else "development")
    app = create_app(config_name)

    if args.prod or config_name == "production":
        from waitress import serve

        print(f"Serving with Waitress on http://{args.host}:{args.port}")
        serve(app, host=args.host, port=args.port, threads=8)
    else:
        print(f"Starting development server on http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
