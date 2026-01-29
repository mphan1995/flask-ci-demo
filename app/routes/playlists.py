from flask import Blueprint, request, jsonify, current_app

playlists_bp = Blueprint("playlists", __name__, url_prefix="/api")


@playlists_bp.get("/playlists")
def list_playlists():
    storage = current_app.extensions["storage"]
    playlists = storage.list_playlists()
    return jsonify([p.__dict__ for p in playlists])


@playlists_bp.post("/playlists")
def create_playlist():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    if not name:
        return jsonify({"error": "missing_name"}), 400
    playlist_id = current_app.extensions["playlist"].create(name)
    return jsonify({"status": "ok", "id": playlist_id})


@playlists_bp.delete("/playlists/<int:playlist_id>")
def delete_playlist(playlist_id: int):
    current_app.extensions["playlist"].delete(playlist_id)
    return jsonify({"status": "ok"})


@playlists_bp.post("/playlists/<int:playlist_id>/items")
def add_item(playlist_id: int):
    payload = request.get_json(silent=True) or {}
    track_id = payload.get("track_id")
    position = int(payload.get("position", 0))
    if not track_id:
        return jsonify({"error": "missing_track_id"}), 400
    item_id = current_app.extensions["playlist"].add_item(playlist_id, track_id, position)
    return jsonify({"status": "ok", "id": item_id})


@playlists_bp.patch("/playlists/<int:playlist_id>/reorder")
def reorder(playlist_id: int):
    payload = request.get_json(silent=True) or {}
    ordered = payload.get("ordered_track_ids", [])
    current_app.extensions["playlist"].reorder(playlist_id, ordered)
    return jsonify({"status": "ok"})

