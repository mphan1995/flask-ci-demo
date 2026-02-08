"""Peer factory to construct runtime objects from specifications."""
from __future__ import annotations

from .models import PeerRuntime, PeerSpec, new_peer_runtime


def build_peer(target: str, video_profile: str, audio_profile: str, metadata: dict | None = None) -> PeerRuntime:
    spec = PeerSpec(target=target, video_profile=video_profile, audio_profile=audio_profile, metadata=metadata or {})
    return new_peer_runtime(spec)
