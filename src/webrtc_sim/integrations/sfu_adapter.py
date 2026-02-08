"""SFU integration adapter placeholder."""
from __future__ import annotations

from typing import Protocol


class SFUAdapter(Protocol):  # pragma: no cover - interface stub
    async def join(self, room: str, peer_id: str):
        ...

    async def leave(self, room: str, peer_id: str):
        ...


class NoopSFUAdapter:
    async def join(self, room: str, peer_id: str):
        return {"status": "joined", "room": room, "peer_id": peer_id}

    async def leave(self, room: str, peer_id: str):
        return {"status": "left", "room": room, "peer_id": peer_id}
