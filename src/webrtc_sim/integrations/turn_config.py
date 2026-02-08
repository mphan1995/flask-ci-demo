"""TURN/STUN configuration helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TurnConfig:
    stun_urls: List[str]
    turn_urls: List[str]
    username: str | None = None
    credential: str | None = None


def from_env(env: dict) -> TurnConfig:
    stun_urls = env.get("WRTC_STUN_URLS", "").split(",") if env.get("WRTC_STUN_URLS") else []
    turn_urls = env.get("WRTC_TURN_URLS", "").split(",") if env.get("WRTC_TURN_URLS") else []
    return TurnConfig(
        stun_urls=[u for u in stun_urls if u],
        turn_urls=[u for u in turn_urls if u],
        username=env.get("WRTC_TURN_USERNAME"),
        credential=env.get("WRTC_TURN_CREDENTIAL"),
    )
