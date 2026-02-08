"""WebSocket signaling endpoints (placeholder)."""
from __future__ import annotations

from flask import Blueprint, jsonify


def create_ws_blueprint():
    bp = Blueprint("signaling_ws", __name__)

    @bp.route("/signal/ws")
    def websocket_placeholder():
        # Placeholder endpoint; real implementation would upgrade to WebSocket using flask-sock or similar.
        return jsonify({"status": "websocket_not_configured"}), 501

    return bp
