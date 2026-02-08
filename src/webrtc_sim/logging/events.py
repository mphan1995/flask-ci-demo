"""Structured logging event helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Mapping

logger = logging.getLogger("webrtc_sim")


@dataclass(frozen=True)
class Event:
    name: str
    payload: Mapping[str, Any]

    def log(self, level: int = logging.INFO) -> None:
        logger.log(level, self.name, extra=self.payload)


# Common event factories

def peer_state_change(peer_id: str, state: str, prev: str | None = None) -> Event:
    return Event(
        name="peer_state_change",
        payload={"peer_id": peer_id, "state": state, "prev_state": prev},
    )


def signaling_message(peer_id: str, session_id: str, direction: str, kind: str) -> Event:
    return Event(
        name="signaling_message",
        payload={"peer_id": peer_id, "session_id": session_id, "direction": direction, "kind": kind},
    )


def metrics_sample(peer_id: str, metrics: Mapping[str, Any]) -> Event:
    return Event(name="metrics_sample", payload={"peer_id": peer_id, **metrics})
