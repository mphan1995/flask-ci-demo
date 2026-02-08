import asyncio

import pytest

from src.webrtc_sim.peers.manager import PeerManager


@pytest.mark.asyncio
async def test_scale_up_and_down():
    manager = PeerManager()
    await manager.scale_peers(3, target="ws://example", video_profile="default-video", audio_profile="default-audio")
    assert manager.registry.count() == 3
    await manager.scale_peers(1, target="ws://example", video_profile="default-video", audio_profile="default-audio")
    assert manager.registry.count() == 1
    await manager.shutdown()
