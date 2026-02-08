"""Metric model definitions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PeerMetrics:
    peer_id: str
    fps: float | None = None
    rtt_ms: float | None = None
    packet_loss: float | None = None
    bitrate_kbps: float | None = None
    negotiation_ms: float | None = None

    def as_dict(self) -> Mapping[str, float | str | None]:
        return self.__dict__
