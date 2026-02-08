"""Control-plane request/response schemas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CreatePeerRequest:
    target: str
    video_profile: str
    audio_profile: str
    metadata: Dict[str, Any] | None = None


@dataclass
class ScaleRequest:
    target_count: int
    target: str
    video_profile: str
    audio_profile: str


@dataclass
class PeerStatus:
    peer_id: str
    state: str
    target: str

    def as_dict(self) -> Dict[str, Any]:
        return {"peer_id": self.peer_id, "state": self.state, "target": self.target}
