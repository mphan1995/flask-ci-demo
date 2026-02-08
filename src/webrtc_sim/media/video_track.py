"""Synthetic video track."""
from __future__ import annotations

import asyncio
from typing import Any

try:
    import av
    from aiortc import MediaStreamTrack
except ImportError:  # pragma: no cover - dependency optional
    av = None

    class MediaStreamTrack:  # type: ignore
        kind = "video"

        async def recv(self):
            return {}

from .frame_generator import FrameGenerator


class SyntheticVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, width: int, height: int, fps: int, pattern: str, peer_id: str | None = None) -> None:
        super().__init__()
        self.generator = FrameGenerator(width=width, height=height, pattern=pattern, peer_id=peer_id)
        self._fps = fps
        self._frame_interval = 1.0 / max(1, fps)

    async def recv(self) -> Any:  # type: ignore
        await asyncio.sleep(self._frame_interval)
        frame = self.generator.next_frame()
        if av:
            video_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
            video_frame.pts = None
            video_frame.time_base = None
            return video_frame
        return {"frame": frame}
