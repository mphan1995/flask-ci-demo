"""Control-plane service logic."""
from __future__ import annotations

from typing import Iterable

from .schemas import CreatePeerRequest, PeerStatus, ScaleRequest
from ..peers.manager import PeerManager


class ControlService:
    def __init__(self, manager: PeerManager) -> None:
        self.manager = manager

    async def create_peer(self, req: CreatePeerRequest) -> str:
        return await self.manager.add_peer(req.target, req.video_profile, req.audio_profile, req.metadata or {})

    async def list_peers(self) -> Iterable[PeerStatus]:
        return [PeerStatus(**peer) for peer in self.manager.list_peers()]

    async def delete_peer(self, peer_id: str) -> None:
        await self.manager.remove_peer(peer_id)

    async def scale(self, req: ScaleRequest) -> None:
        await self.manager.scale_peers(req.target_count, req.target, req.video_profile, req.audio_profile)
