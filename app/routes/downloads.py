from flask import Blueprint, request, jsonify, current_app

from app.utils.validators import is_safe_url, allowed_extension


downloads_bp = Blueprint("downloads", __name__, url_prefix="/api")


@downloads_bp.get("/downloads")
def list_downloads():
    storage = current_app.extensions["storage"]
    jobs = storage.list_downloads()
    return jsonify([job.__dict__ for job in jobs])


@downloads_bp.post("/downloads")
def create_download():
    payload = request.get_json(silent=True) or {}
    url = payload.get("url")
    mode = payload.get("mode", "direct")
    if not url:
        return jsonify({"error": "missing_url"}), 400

    cfg = current_app.config
    if not is_safe_url(url, allow_private=not cfg["LAN_ONLY"]):
        return jsonify({"error": "unsafe_url"}), 400

    if mode in {"direct", "cache"}:
        if not allowed_extension(url, cfg["DOWNLOAD_ALLOWED_EXT"]):
            return jsonify({"error": "unsupported_extension"}), 400

        manager = current_app.extensions["downloads"]
        target_dir = cfg["LOCAL_MUSIC_DIR"] if mode == "direct" else cfg["CACHE_DIR"]
        job_id = manager.enqueue(url, mode, target_dir, cfg["DOWNLOAD_MAX_SIZE_MB"])
        return jsonify({"status": "ok", "id": job_id})

    if mode == "stream":
        # Streaming URL: store metadata only for playback engine
        return jsonify({"status": "ok", "message": "stream_mode_not_implemented"}), 202

    return jsonify({"error": "invalid_mode"}), 400


@downloads_bp.delete("/downloads/<int:job_id>")
def cancel_download(job_id: int):
    # TODO: implement cancel
    current_app.extensions["storage"].update_download(job_id, status="canceled")
    return jsonify({"status": "ok"})

