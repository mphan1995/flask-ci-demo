from flask import Blueprint, request, jsonify, current_app

from app.utils.validators import is_safe_url, classify_url


downloads_bp = Blueprint("downloads", __name__, url_prefix="/api")


@downloads_bp.get("/downloads")
def list_downloads():
    storage = current_app.extensions["storage"]
    jobs = storage.list_downloads()
    return jsonify([job.__dict__ for job in jobs])


@downloads_bp.post("/downloads")
def create_download():
    payload = request.get_json(silent=True) or {}
    raw_url = payload.get("url")
    mode = payload.get("mode", "direct")
    if not raw_url:
        return jsonify({"error": "missing_url", "message": "Link không hợp lệ"}), 400

    cfg = current_app.config
    info = classify_url(raw_url, cfg["DOWNLOAD_ALLOWED_EXT"])
    if not info.get("valid"):
        return jsonify({"error": "invalid_link", "message": "Link không hợp lệ"}), 400

    url = info["url"]
    if not is_safe_url(url, allow_private=not cfg["LAN_ONLY"]):
        return jsonify({"error": "unsafe_url", "message": "Link không hợp lệ"}), 400

    if info["kind"] in {"youtube", "nhaccuatui", "zingmp3"}:
        # Require legal adapter/integration for these sources
        return jsonify({
            "status": "accepted",
            "source": info["kind"],
            "message": "Nguon hop le, can adapter hop phap de tai.",
        }), 202

    if info["kind"] == "audio":
        if mode not in {"direct", "cache"}:
            return jsonify({"error": "invalid_mode", "message": "Che do khong hop le"}), 400
        manager = current_app.extensions["downloads"]
        target_dir = cfg["LOCAL_MUSIC_DIR"] if mode == "direct" else cfg["CACHE_DIR"]
        job_id = manager.enqueue(url, mode, target_dir, cfg["DOWNLOAD_MAX_SIZE_MB"])
        return jsonify({"status": "ok", "id": job_id})

    return jsonify({"error": "invalid_link", "message": "Link không hợp lệ"}), 400


@downloads_bp.delete("/downloads/<int:job_id>")
def cancel_download(job_id: int):
    # TODO: implement cancel
    current_app.extensions["storage"].update_download(job_id, status="canceled")
    return jsonify({"status": "ok"})
