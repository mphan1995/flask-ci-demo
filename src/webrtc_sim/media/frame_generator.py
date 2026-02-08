"""Frame generation utilities for synthetic video."""
from __future__ import annotations

import itertools
import numpy as np

from . import patterns, overlays


class FrameGenerator:
    def __init__(self, width: int = 640, height: int = 480, pattern: str = "color_bars", peer_id: str | None = None):
        self.width = width
        self.height = height
        self.pattern = pattern
        self.peer_id = peer_id
        self._counter = itertools.count()

    def next_frame(self):
        idx = next(self._counter)
        if self.pattern == "color_bars":
            frame = patterns.color_bars(self.width, self.height)
        else:
            frame = patterns.solid((0, 128, 255), self.width, self.height)
        frame = overlays.apply_overlays(frame, peer_id=self.peer_id, frame_idx=idx)
        return frame
