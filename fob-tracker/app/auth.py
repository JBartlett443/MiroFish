"""Simple admin session auth + decorators."""
from functools import wraps
from datetime import datetime

from flask import current_app, jsonify, redirect, request, session, url_for

from . import db


def login(username: str, password: str) -> bool:
    if (
        username == current_app.config["ADMIN_USERNAME"]
        and password == current_app.config["ADMIN_PASSWORD"]
    ):
        session["admin"] = username
        return True
    return False


def logout():
    session.pop("admin", None)


def current_admin() -> str | None:
    return session.get("admin")


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_admin():
            return redirect(url_for("admin.login_view", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def require_api_key(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        from . import api_keys

        key = request.headers.get("X-API-Key", "")
        key_id = api_keys.verify(key)
        if key_id is None:
            resp = jsonify({"error": "unauthorized"})
            resp.status_code = 401
            resp.headers["X-Fob-Api"] = "1"
            return resp
        db.execute(
            "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), key_id),
        )
        response = view(*args, **kwargs)
        try:
            response.headers["X-Fob-Api"] = "1"
        except AttributeError:
            pass
        return response

    return wrapped
