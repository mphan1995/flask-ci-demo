from pathlib import Path

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

library_bp = Blueprint("library", __name__, url_prefix="/api")


@library_bp.get("/tracks")
def tracks():
    query = request.args.get("query")
    source = request.args.get("source")
    storage = current_app.extensions["storage"]
    items = storage.list_tracks(query=query, source=source)
    return jsonify([item.__dict__ for item in items])


@library_bp.post("/upload")
def upload():
    if "file" not in request.files:
        return jsonify({"error": "missing_file"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "missing_filename"}), 400

    cfg = current_app.config
    filename = secure_filename(file.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in cfg["DOWNLOAD_ALLOWED_EXT"]:
        return jsonify({"error": "unsupported_format"}), 400

    target_dir = Path(cfg["LOCAL_MUSIC_DIR"])
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / filename
    file.save(dest)

    library = current_app.extensions["library"]
    track_id = library.add_local_file(dest)
    return jsonify({"status": "ok", "track_id": track_id})


@library_bp.post("/scan")
def scan():
    cfg = current_app.config
    library = current_app.extensions["library"]
    new_ids = library.scan_local(cfg["DOWNLOAD_ALLOWED_EXT"])
    return jsonify({"status": "ok", "imported": len(new_ids)})

