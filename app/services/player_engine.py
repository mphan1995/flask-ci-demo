from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import time


@dataclass
class PlayerState:
    status: str = "idle"  # idle | playing | paused | error
    track_id: Optional[int] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    position: float = 0.0
    duration: Optional[float] = None
    volume: int = 70
    repeat_mode: str = "off"  # off | one | all
    shuffle: bool = False
    updated_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["updated_at"] = self.updated_at
        return data


class PlayerEngine:
    """
    Skeleton engine. Replace internals with VLC/mpg123/ffplay integration.
    """
    def __init__(self, event_bus=None, default_volume: int = 70):
        self.state = PlayerState(volume=default_volume, updated_at=time.time())
        self.event_bus = event_bus

    def _emit(self):
        self.state.updated_at = time.time()
        if self.event_bus:
            self.event_bus.publish("player", self.state.to_dict())

    def play(self, track_info: Dict[str, Any]):
        self.state.status = "playing"
        self.state.track_id = track_info.get("id")
        self.state.title = track_info.get("title")
        self.state.artist = track_info.get("artist")
        self.state.duration = track_info.get("duration")
        self.state.position = 0
        self._emit()

    def pause(self):
        self.state.status = "paused"
        self._emit()

    def resume(self):
        self.state.status = "playing"
        self._emit()

    def stop(self):
        self.state.status = "idle"
        self.state.position = 0
        self._emit()

    def seek(self, position: float):
        self.state.position = max(0.0, position)
        self._emit()

    def set_volume(self, volume: int):
        self.state.volume = max(0, min(100, volume))
        self._emit()

    def set_repeat(self, mode: str):
        if mode in {"off", "one", "all"}:
            self.state.repeat_mode = mode
            self._emit()

    def set_shuffle(self, enabled: bool):
        self.state.shuffle = bool(enabled)
        self._emit()

    def next(self):
        # TODO: integrate queue management
        self._emit()

    def prev(self):
        # TODO: integrate queue management
        self._emit()

