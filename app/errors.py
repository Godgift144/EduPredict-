"""Error handlers (HTML pages for browsers, JSON for API clients)."""
from __future__ import annotations

from flask import jsonify, render_template, request


def _wants_json() -> bool:
    return (
        request.path.startswith("/api/")
        or "application/json" in (request.accept_mimetypes.best or "")
    )


def register_error_handlers(app) -> None:
    @app.errorhandler(404)
    def not_found(err):  # pragma: no cover - trivial
        if _wants_json():
            return jsonify(error="Not found", message=str(err)), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(err):  # pragma: no cover - trivial
        if _wants_json():
            return jsonify(error="Forbidden", message=str(err)), 403
        return render_template("errors/404.html"), 403

    @app.errorhandler(500)
    def server_error(err):  # pragma: no cover - trivial
        if _wants_json():
            return jsonify(error="Internal server error"), 500
        return render_template("errors/500.html"), 500
