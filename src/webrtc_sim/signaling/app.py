"""Flask application factory for signaling, control, and UI."""
from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify, redirect

from .http_routes import create_http_blueprint
from .ws_routes import create_ws_blueprint
from .session_store import SessionStore

logger = logging.getLogger(__name__)


def _web_paths():
    base = Path(__file__).resolve().parent.parent / "web"
    return {
        "template_folder": str(base / "templates"),
        "static_folder": str(base / "static"),
        "static_url_path": "/static",
    }


def create_signaling_app(session_ttl: int = 180) -> Flask:
    paths = _web_paths()
    app = Flask(__name__, **paths)
    session_store = SessionStore(ttl_seconds=session_ttl)

    app.register_blueprint(create_http_blueprint(session_store))
    app.register_blueprint(create_ws_blueprint())

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/")
    def root():
        return redirect("/ui", code=302)

    return app
