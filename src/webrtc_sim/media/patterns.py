"""Synthetic video pattern helpers."""
from __future__ import annotations

import numpy as np


def color_bars(width: int, height: int):
    bars = np.array(
        [
            [255, 255, 0],  # yellow
            [0, 255, 255],  # cyan
            [255, 0, 255],  # magenta
            [0, 255, 0],    # green
            [0, 0, 255],    # blue
            [255, 0, 0],    # red
            [255, 255, 255],  # white
        ],
        dtype=np.uint8,
    )
    bar_width = max(1, width // len(bars))
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for idx, color in enumerate(bars):
        frame[:, idx * bar_width : (idx + 1) * bar_width] = color
    return frame


def solid(color: tuple[int, int, int], width: int, height: int):
    return np.full((height, width, 3), color, dtype=np.uint8)
