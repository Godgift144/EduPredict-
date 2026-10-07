"""Role-based access control helpers."""
from __future__ import annotations

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def roles_required(*roles: str):
    """Require the current user to have one of the given roles."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("main.dashboard"))
            return view(*args, **kwargs)

        return wrapped

    return decorator
