from flask import Flask

from app.config import Config
from app.db import init_db
from app.services.storage import Storage
from app.services.player_engine import PlayerEngine
from app.services.library_manager import LibraryManager
from app.services.playlist_manager import PlaylistManager
from app.services.download_manager import DownloadManager
from app.realtime.sse import EventBus
from app.routes import register_routes


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # Ensure directories exist
    app.config["LOCAL_MUSIC_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["CACHE_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["DATA_DIR"].mkdir(parents=True, exist_ok=True)

    init_db(app.config["DB_PATH"])

    events = EventBus()
    storage = Storage(app.config["DB_PATH"])
    player = PlayerEngine(event_bus=events, default_volume=app.config["DEFAULT_VOLUME"])
    library = LibraryManager(app.config["LOCAL_MUSIC_DIR"], storage)
    playlist = PlaylistManager(storage)
    downloads = DownloadManager(storage, event_bus=events)

    app.extensions["events"] = events
    app.extensions["storage"] = storage
    app.extensions["player"] = player
    app.extensions["library"] = library
    app.extensions["playlist"] = playlist
    app.extensions["downloads"] = downloads

    register_routes(app)
    return app

