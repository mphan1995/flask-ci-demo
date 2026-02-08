"""Media profile models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class VideoProfile:
    width: int
    height: int
    fps: int
    pattern: str


@dataclass(frozen=True)
class AudioProfile:
    sample_rate: int
    channels: int
    profile: str
    tone_hz: int | None = None


@dataclass(frozen=True)
class MediaProfile:
    video: VideoProfile
    audio: AudioProfile


def from_dict(video: Mapping[str, Any], audio: Mapping[str, Any]) -> MediaProfile:
    video_profile = VideoProfile(
        width=int(video.get("width", 640)),
        height=int(video.get("height", 480)),
        fps=int(video.get("fps", 30)),
        pattern=video.get("pattern", "color_bars"),
    )
    audio_profile = AudioProfile(
        sample_rate=int(audio.get("sample_rate", 48000)),
        channels=int(audio.get("channels", 1)),
        profile=audio.get("profile", "tone"),
        tone_hz=audio.get("tone_hz", 440),
    )
    return MediaProfile(video=video_profile, audio=audio_profile)
