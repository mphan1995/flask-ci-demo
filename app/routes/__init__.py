from flask import Blueprint

from app.routes.playback import playback_bp
from app.routes.library import library_bp
from app.routes.playlists import playlists_bp
from app.routes.downloads import downloads_bp
from app.routes.realtime import realtime_bp
from app.routes.ui import ui_bp


def register_routes(app):
    app.register_blueprint(ui_bp)
    app.register_blueprint(playback_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(playlists_bp)
    app.register_blueprint(downloads_bp)
    app.register_blueprint(realtime_bp)

