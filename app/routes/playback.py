from flask import Blueprint, request, jsonify, current_app

playback_bp = Blueprint("playback", __name__, url_prefix="/api")


@playback_bp.post("/play")
def play():
    payload = request.get_json(silent=True) or {}
    track_id = payload.get("track_id")
    storage = current_app.extensions["storage"]
    player = current_app.extensions["player"]

    track = storage.get_track(track_id) if track_id else None
    if not track:
        return jsonify({"error": "track_not_found"}), 404

    player.play({
        "id": track.id,
        "title": track.title,
        "artist": track.artist,
        "duration": track.duration,
    })
    return jsonify({"status": "ok"})


@playback_bp.post("/pause")
def pause():
    current_app.extensions["player"].pause()
    return jsonify({"status": "ok"})


@playback_bp.post("/resume")
def resume():
    current_app.extensions["player"].resume()
    return jsonify({"status": "ok"})


@playback_bp.post("/next")
def next_track():
    current_app.extensions["player"].next()
    return jsonify({"status": "ok"})


@playback_bp.post("/prev")
def prev_track():
    current_app.extensions["player"].prev()
    return jsonify({"status": "ok"})


@playback_bp.post("/seek")
def seek():
    payload = request.get_json(silent=True) or {}
    position = float(payload.get("position_seconds", 0))
    current_app.extensions["player"].seek(position)
    return jsonify({"status": "ok"})


@playback_bp.post("/volume")
def volume():
    payload = request.get_json(silent=True) or {}
    volume = int(payload.get("volume", 0))
    current_app.extensions["player"].set_volume(volume)
    return jsonify({"status": "ok"})


@playback_bp.post("/repeat")
def repeat():
    payload = request.get_json(silent=True) or {}
    mode = payload.get("mode", "off")
    current_app.extensions["player"].set_repeat(mode)
    return jsonify({"status": "ok"})


@playback_bp.post("/shuffle")
def shuffle():
    payload = request.get_json(silent=True) or {}
    enabled = bool(payload.get("enabled", False))
    current_app.extensions["player"].set_shuffle(enabled)
    return jsonify({"status": "ok"})


@playback_bp.get("/status")
def status():
    player = current_app.extensions["player"]
    return jsonify(player.state.to_dict())

