import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = Path(os.getenv("MUSICBOX_DATA_DIR", BASE_DIR / "data"))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JSON_SORT_KEYS = False
    DATA_DIR = DEFAULT_DATA_DIR
    LOCAL_MUSIC_DIR = Path(os.getenv("MUSICBOX_LOCAL_DIR", DEFAULT_DATA_DIR / "local"))
    CACHE_DIR = Path(os.getenv("MUSICBOX_CACHE_DIR", DEFAULT_DATA_DIR / "cache"))
    DB_PATH = Path(os.getenv("MUSICBOX_DB_PATH", DEFAULT_DATA_DIR / "db.sqlite"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 1024 * 1024 * 1024))  # 1GB
    DOWNLOAD_MAX_SIZE_MB = int(os.getenv("DOWNLOAD_MAX_SIZE_MB", 500))
    DOWNLOAD_ALLOWED_EXT = {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"}
    LAN_ONLY = os.getenv("LAN_ONLY", "true").lower() == "true"
    DEFAULT_VOLUME = int(os.getenv("DEFAULT_VOLUME", 70))
    CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", 72))
    CACHE_MAX_GB = int(os.getenv("CACHE_MAX_GB", 10))

