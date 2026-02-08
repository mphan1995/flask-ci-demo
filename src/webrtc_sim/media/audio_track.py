"""Synthetic audio track."""
from __future__ import annotations

import asyncio
import numpy as np
from typing import Any

try:
    import av
    from aiortc import MediaStreamTrack
except ImportError:  # pragma: no cover
    av = None

    class MediaStreamTrack:  # type: ignore
        kind = "audio"

        async def recv(self):
            return {}


class SyntheticAudioTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, sample_rate: int, channels: int, profile: str = "tone", tone_hz: int = 440) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.profile = profile
        self.tone_hz = tone_hz
        self._frame_duration = 0.02  # 20 ms
        self._t = 0

    async def recv(self) -> Any:  # type: ignore
        await asyncio.sleep(self._frame_duration)
        samples = self._generate_samples()
        if av:
            frame = av.AudioFrame.from_ndarray(samples, layout="mono" if self.channels == 1 else "stereo")
            frame.sample_rate = self.sample_rate
            return frame
        return {"samples": samples}

    def _generate_samples(self):
        num_samples = int(self.sample_rate * self._frame_duration)
        if self.profile == "silence":
            return np.zeros(num_samples, dtype=np.float32)
        t = (np.arange(num_samples) + self._t) / self.sample_rate
        self._t += num_samples
        wave = 0.1 * np.sin(2 * np.pi * self.tone_hz * t)
        return wave.astype(np.float32)
