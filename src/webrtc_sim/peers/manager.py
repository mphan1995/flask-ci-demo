"""Peer manager orchestrates peer creation and lifecycle."""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from .factory import build_peer
from .lifecycle import PeerLifecycle
from .registry import PeerRegistry
from ..runtime.task_supervisor import TaskSupervisor

logger = logging.getLogger(__name__)


class PeerManager:
    def __init__(self, registry: PeerRegistry | None = None, supervisor: TaskSupervisor | None = None) -> None:
        self.registry = registry or PeerRegistry()
        self.lifecycle = PeerLifecycle(self.registry)
        self.supervisor = supervisor or TaskSupervisor()

    def list_peers(self) -> Iterable[dict]:
        return [
            {"peer_id": peer.peer_id, "state": peer.state, "target": peer.spec.target}
            for peer in self.registry.all()
        ]

    async def add_peer(self, target: str, video_profile: str, audio_profile: str, metadata: dict | None = None):
        peer = build_peer(target, video_profile, audio_profile, metadata)
        self.registry.add(peer)
        self.supervisor.create(f"peer-{peer.peer_id}", self.lifecycle.start_peer(peer))
        return peer.peer_id

    async def remove_peer(self, peer_id: str) -> None:
        await self.lifecycle.stop_peer(peer_id)

    async def scale_peers(self, target_count: int, target: str, video_profile: str, audio_profile: str) -> None:
        current = self.registry.count()
        if target_count > current:
            for _ in range(target_count - current):
                await self.add_peer(target, video_profile, audio_profile)
        elif target_count < current:
            ids = [p.peer_id for p in list(self.registry.all())[: current - target_count]]
            await asyncio.gather(*(self.remove_peer(pid) for pid in ids))

    async def shutdown(self) -> None:
        for peer in list(self.registry.all()):
            await self.remove_peer(peer.peer_id)
        await self.supervisor.shutdown()
