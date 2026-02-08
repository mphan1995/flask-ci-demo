"""Peer registry for active runtimes."""
from __future__ import annotations

from typing import Dict, Iterable

from .models import PeerRuntime


class PeerRegistry:
    def __init__(self) -> None:
        self._peers: Dict[str, PeerRuntime] = {}

    def add(self, peer: PeerRuntime) -> None:
        self._peers[peer.peer_id] = peer

    def get(self, peer_id: str) -> PeerRuntime | None:
        return self._peers.get(peer_id)

    def remove(self, peer_id: str) -> None:
        self._peers.pop(peer_id, None)

    def all(self) -> Iterable[PeerRuntime]:
        return list(self._peers.values())

    def count(self) -> int:
        return len(self._peers)


def create_registry() -> PeerRegistry:
    return PeerRegistry()
