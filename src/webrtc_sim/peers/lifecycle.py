"""Peer lifecycle control."""
from __future__ import annotations

import asyncio
import logging
import time

from .models import PeerRuntime
from .state_machine import can_transition

logger = logging.getLogger(__name__)


class PeerLifecycle:
    def __init__(self, registry) -> None:
        self.registry = registry

    async def start_peer(self, peer: PeerRuntime) -> PeerRuntime:
        await self._transition(peer, "preparing")
        await self._prepare(peer)
        await self._transition(peer, "signaling")
        await self._simulate_signaling(peer)
        await self._transition(peer, "negotiating")
        await self._transition(peer, "connected")
        await self._transition(peer, "streaming")
        return peer

    async def stop_peer(self, peer_id: str) -> None:
        peer = self.registry.get(peer_id)
        if not peer:
            return
        await self._transition(peer, "stopping")
        await peer.close()
        await self._transition(peer, "stopped")
        self.registry.remove(peer.peer_id)

    async def _prepare(self, peer: PeerRuntime) -> None:
        # Placeholder for track and transport setup
        await asyncio.sleep(0)

    async def _simulate_signaling(self, peer: PeerRuntime) -> None:
        # Placeholder for offer/answer exchange integration with signaling layer
        await asyncio.sleep(0.01)

    async def _transition(self, peer: PeerRuntime, target: str) -> None:
        if not can_transition(peer.state, target):
            logger.warning("invalid transition", extra={"peer_id": peer.peer_id, "from": peer.state, "to": target})
            return
        await peer.set_state(target)
        if target in {"streaming", "connected"}:
            peer.created_at = peer.created_at or time.time()
