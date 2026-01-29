from __future__ import annotations

from pathlib import Path
from typing import List

from app.models import Track


class LibraryManager:
    def __init__(self, local_dir: Path, storage):
        self.local_dir = local_dir
        self.storage = storage

    def scan_local(self, allowed_ext: set) -> List[int]:
        self.local_dir.mkdir(parents=True, exist_ok=True)
        new_ids = []
        for path in self.local_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in allowed_ext:
                title = path.stem
                track = Track(
                    id=None,
                    title=title,
                    artist=None,
                    album=None,
                    duration=None,
                    cover_path=None,
                    source_type="local",
                    source_url=None,
                    local_path=str(path),
                )
                new_id = self.storage.create_track(track)
                new_ids.append(new_id)
        return new_ids

    def add_local_file(self, file_path: Path) -> int:
        title = file_path.stem
        track = Track(
            id=None,
            title=title,
            artist=None,
            album=None,
            duration=None,
            cover_path=None,
            source_type="local",
            source_url=None,
            local_path=str(file_path),
        )
        return self.storage.create_track(track)

