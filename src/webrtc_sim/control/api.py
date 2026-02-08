"""HTTP API for control plane."""
from __future__ import annotations

import asyncio
from flask import Blueprint, jsonify, request

from .schemas import CreatePeerRequest, ScaleRequest
from .service import ControlService


def create_control_blueprint(service: ControlService) -> Blueprint:
    bp = Blueprint("control_api", __name__)

    def run_async(coro):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        if loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, loop).result()
        return loop.run_until_complete(coro)

    @bp.route("/control/peers", methods=["GET"])
    def list_peers():
        peers = run_async(service.list_peers())
        return jsonify([p.as_dict() for p in peers])

    @bp.route("/control/peers", methods=["POST"])
    def create_peer():
        payload = request.get_json(force=True)
        req = CreatePeerRequest(
            target=payload.get("target", ""),
            video_profile=payload.get("video_profile", "default-video"),
            audio_profile=payload.get("audio_profile", "default-audio"),
            metadata=payload.get("metadata", {}),
        )
        peer_id = run_async(service.create_peer(req))
        return jsonify({"peer_id": peer_id}), 201

    @bp.route("/control/peers/<peer_id>", methods=["DELETE"])
    def delete_peer(peer_id: str):
        run_async(service.delete_peer(peer_id))
        return jsonify({"status": "deleted", "peer_id": peer_id})

    @bp.route("/control/scale", methods=["POST"])
    def scale():
        payload = request.get_json(force=True)
        req = ScaleRequest(
            target_count=int(payload.get("target_count", 1)),
            target=payload.get("target", ""),
            video_profile=payload.get("video_profile", "default-video"),
            audio_profile=payload.get("audio_profile", "default-audio"),
        )
        run_async(service.scale(req))
        return jsonify({"status": "scaled", "target_count": req.target_count})

    return bp
