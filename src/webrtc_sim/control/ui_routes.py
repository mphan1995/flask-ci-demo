"""UI routes for interactive browser control."""
from __future__ import annotations

from pathlib import Path
from flask import Blueprint, render_template


def _template_dir() -> str:
    return str(Path(__file__).resolve().parent.parent / "web" / "templates")


def create_ui_blueprint() -> Blueprint:
    bp = Blueprint("control_ui", __name__, template_folder=_template_dir())

    @bp.route("/ui")
    def index():
        return render_template("index.html")

    return bp
