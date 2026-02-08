"""Adapter from WebRTC stats objects to internal metrics."""
from __future__ import annotations

from typing import Any

from .models import PeerMetrics


def from_aiortc(peer_id: str, stats: Any) -> PeerMetrics:
    # stats is expected to be the output of RTCPeerConnection.getStats()
    # To keep the skeleton lightweight, we pull only common fields if present.
    rtt = None
    bitrate = None
    packet_loss = None
    fps = None

    for report in getattr(stats, "values", lambda: stats.values())():
        report_type = getattr(report, "type", None) or getattr(report, "__class__", type("", (), {})).__name__
        if report_type == "outbound-rtp" or report_type == "outboundRtp":
            fps = getattr(report, "framesPerSecond", fps)
            bitrate = getattr(report, "bitrate", bitrate)
            packet_loss = getattr(report, "packetsLost", packet_loss)
        if report_type == "candidate-pair" or report_type == "candidatePair":
            rtt = getattr(report, "currentRoundTripTime", rtt)

    return PeerMetrics(peer_id=peer_id, fps=fps, rtt_ms=_ms(rtt), packet_loss=packet_loss, bitrate_kbps=_kbps(bitrate))


def _ms(value):
    return None if value is None else float(value) * 1000.0


def _kbps(value):
    return None if value is None else float(value) / 1000.0
