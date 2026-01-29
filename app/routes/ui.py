from flask import Blueprint, render_template

ui_bp = Blueprint("ui", __name__)


@ui_bp.get("/")
def now_playing():
    return render_template("now_playing.html")


@ui_bp.get("/library")
def library():
    return render_template("library.html")


@ui_bp.get("/playlists")
def playlists():
    return render_template("playlists.html")


@ui_bp.get("/downloads")
def downloads():
    return render_template("downloads.html")


@ui_bp.get("/settings")
def settings():
    return render_template("settings.html")

