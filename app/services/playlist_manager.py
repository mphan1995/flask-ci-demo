from __future__ import annotations

from typing import Iterable


class PlaylistManager:
    def __init__(self, storage):
        self.storage = storage

    def create(self, name: str) -> int:
        return self.storage.create_playlist(name)

    def delete(self, playlist_id: int) -> None:
        self.storage.delete_playlist(playlist_id)

    def add_item(self, playlist_id: int, track_id: int, position: int) -> int:
        return self.storage.add_playlist_item(playlist_id, track_id, position)

    def reorder(self, playlist_id: int, ordered_track_ids: Iterable[int]) -> None:
        self.storage.reorder_playlist(playlist_id, ordered_track_ids)

