"""Peer domain models."""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

try:  # aiortc is optional until runtime
    from aiortc import RTCPeerConnection
except ImportError:  # pragma: no cover - fallback stub
    class RTCPeerConnection:  # type: ignore
        def __init__(self) -> None:
            self._stats = {}

        async def setRemoteDescription(self, *_: Any, **__: Any) -> None:
            return None

        async def setLocalDescription(self, *_: Any, **__: Any) -> None:
            return None

        async def close(self) -> None:
            return None

        async def getStats(self) -> dict:
            return self._stats

        def addTrack(self, *_: Any, **__: Any) -> None:
            return None


@dataclass(frozen=True)
class PeerSpec:
    target: str  # signaling target endpoint
    video_profile: str
    audio_profile: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PeerRuntime:
    peer_id: str
    spec: PeerSpec
    pc: RTCPeerConnection
    state: str = "created"
    created_at: float | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def set_state(self, state: str) -> None:
        async with self._lock:
            self.state = state

    async def close(self) -> None:
        async with self._lock:
            await self.pc.close()
            self.state = "stopped"

    async def get_stats(self) -> Any:
        return await self.pc.getStats()


def new_peer_runtime(spec: PeerSpec) -> PeerRuntime:
    return PeerRuntime(peer_id=str(uuid.uuid4()), spec=spec, pc=RTCPeerConnection())
