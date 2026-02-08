"""HTTP signaling endpoints."""
from __future__ import annotations

import uuid
from flask import Blueprint, jsonify, request

from .session_store import SessionStore
from .schemas import OfferRequest, AnswerResponse, IceCandidate


def create_http_blueprint(session_store: SessionStore) -> Blueprint:
    bp = Blueprint("signaling_http", __name__)

    @bp.route("/signal/offer", methods=["POST"])
    def offer():
        payload = request.get_json(force=True)
        offer_req = OfferRequest(peer_id=payload.get("peer_id"), sdp=payload.get("sdp", ""), type=payload.get("type", "offer"))
        session_id = payload.get("session_id") or str(uuid.uuid4())
        session_store.create(session_id=session_id, peer_id=offer_req.peer_id)
        # In a real implementation we would pass offer to peer connection and generate answer.
        answer = AnswerResponse(sdp="v=0\n")
        return jsonify({"session_id": session_id, "answer": answer.as_dict()})

    @bp.route("/signal/candidate", methods=["POST"])
    def candidate():
        payload = request.get_json(force=True)
        session_id = payload.get("session_id")
        session = session_store.get(session_id)
        if not session:
            return jsonify({"error": "invalid_session"}), 404
        candidate = IceCandidate(candidate=payload.get("candidate", ""), sdpMid=payload.get("sdpMid"), sdpMLineIndex=payload.get("sdpMLineIndex"))
        # Placeholder: in full implementation, forward to peer connection
        return jsonify({"status": "queued", "session_id": session_id, "candidate": candidate.as_dict()})

    @bp.route("/signal/session/<session_id>", methods=["DELETE"])
    def delete_session(session_id: str):
        session_store.delete(session_id)
        return jsonify({"status": "deleted", "session_id": session_id})

    return bp
