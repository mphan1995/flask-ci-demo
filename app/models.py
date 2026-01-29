from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    id: Optional[int]
    title: str
    artist: Optional[str]
    album: Optional[str]
    duration: Optional[int]
    cover_path: Optional[str]
    source_type: str  # local | remote | stream
    source_url: Optional[str]
    local_path: Optional[str]
    created_at: Optional[str] = None


@dataclass
class Playlist:
    id: Optional[int]
    name: str
    created_at: Optional[str] = None


@dataclass
class PlaylistItem:
    id: Optional[int]
    playlist_id: int
    track_id: int
    position: int


@dataclass
class DownloadJob:
    id: Optional[int]
    url: str
    mode: str  # direct | cache
    status: str  # queued | downloading | done | failed | canceled
    progress: float
    local_path: Optional[str]
    error: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
