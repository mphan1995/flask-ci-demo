"""Overlay helpers for synthetic frames."""
from __future__ import annotations

import cv2
import time


def apply_overlays(frame, peer_id: str | None = None, frame_idx: int | None = None, timestamp: bool = True):
    if frame is None:
        return frame
    text_parts = []
    if peer_id:
        text_parts.append(f"peer:{peer_id}")
    if frame_idx is not None:
        text_parts.append(f"f:{frame_idx}")
    if timestamp:
        text_parts.append(time.strftime("%H:%M:%S"))
    label = " | ".join(text_parts)
    if not label:
        return frame
    cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    return frame
