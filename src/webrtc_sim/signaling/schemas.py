"""Signaling payload schemas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class OfferRequest:
    peer_id: str
    sdp: str
    type: str


@dataclass
class AnswerResponse:
    sdp: str
    type: str = "answer"

    def as_dict(self) -> Dict[str, Any]:
        return {"sdp": self.sdp, "type": self.type}


@dataclass
class IceCandidate:
    candidate: str
    sdpMid: str | None = None
    sdpMLineIndex: int | None = None

    def as_dict(self) -> Dict[str, Any]:
        data = {"candidate": self.candidate}
        if self.sdpMid:
            data["sdpMid"] = self.sdpMid
        if self.sdpMLineIndex is not None:
            data["sdpMLineIndex"] = self.sdpMLineIndex
        return data
