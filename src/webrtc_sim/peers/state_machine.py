"""Peer state machine rules."""
from __future__ import annotations

from typing import Set


ALLOWED_TRANSITIONS: dict[str, Set[str]] = {
    "created": {"preparing", "failed", "stopping"},
    "preparing": {"signaling", "failed", "stopping"},
    "signaling": {"negotiating", "failed", "stopping"},
    "negotiating": {"connected", "failed", "stopping"},
    "connected": {"streaming", "degraded", "stopping", "failed"},
    "streaming": {"degraded", "stopping", "failed"},
    "degraded": {"streaming", "stopping", "failed"},
    "stopping": {"stopped"},
    "stopped": set(),
    "failed": {"stopping", "stopped"},
}


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())
