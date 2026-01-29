from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable, List, Optional

from pathlib import Path
import sqlite3

from app.models import Track, Playlist, PlaylistItem, DownloadJob
from app.db import connect


class Storage:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    @contextmanager
    def _conn(self):
        conn = connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def list_tracks(self, query: Optional[str] = None, source: Optional[str] = None) -> List[Track]:
        sql = "SELECT * FROM tracks"
        params: list = []
        clauses: list = []
        if query:
            clauses.append("(title LIKE ? OR artist LIKE ? OR album LIKE ?)")
            like = f"%{query}%"
            params.extend([like, like, like])
        if source:
            clauses.append("source_type = ?")
            params.append(source)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id DESC"
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [Track(**dict(row)) for row in rows]

    def get_track(self, track_id: int) -> Optional[Track]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM tracks WHERE id = ?", (track_id,)).fetchone()
        return Track(**dict(row)) if row else None

    def create_track(self, track: Track) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tracks (title, artist, album, duration, cover_path, source_type, source_url, local_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    track.title,
                    track.artist,
                    track.album,
                    track.duration,
                    track.cover_path,
                    track.source_type,
                    track.source_url,
                    track.local_path,
                ),
            )
        return cursor.lastrowid

    def list_playlists(self) -> List[Playlist]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM playlists ORDER BY id DESC").fetchall()
        return [Playlist(**dict(row)) for row in rows]

    def create_playlist(self, name: str) -> int:
        with self._conn() as conn:
            cursor = conn.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
        return cursor.lastrowid

    def delete_playlist(self, playlist_id: int) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM playlist_items WHERE playlist_id = ?", (playlist_id,))
            conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))

    def add_playlist_item(self, playlist_id: int, track_id: int, position: int) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO playlist_items (playlist_id, track_id, position) VALUES (?, ?, ?)",
                (playlist_id, track_id, position),
            )
        return cursor.lastrowid

    def reorder_playlist(self, playlist_id: int, ordered_track_ids: Iterable[int]) -> None:
        with self._conn() as conn:
            for idx, track_id in enumerate(ordered_track_ids):
                conn.execute(
                    "UPDATE playlist_items SET position = ? WHERE playlist_id = ? AND track_id = ?",
                    (idx, playlist_id, track_id),
                )

    def list_downloads(self) -> List[DownloadJob]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM downloads ORDER BY id DESC").fetchall()
        return [DownloadJob(**dict(row)) for row in rows]

    def create_download(self, job: DownloadJob) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO downloads (url, mode, status, progress, local_path, error)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (job.url, job.mode, job.status, job.progress, job.local_path, job.error),
            )
        return cursor.lastrowid

    def update_download(self, job_id: int, *, status: Optional[str] = None, progress: Optional[float] = None,
                        local_path: Optional[str] = None, error: Optional[str] = None) -> None:
        fields = []
        params = []
        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if progress is not None:
            fields.append("progress = ?")
            params.append(progress)
        if local_path is not None:
            fields.append("local_path = ?")
            params.append(local_path)
        if error is not None:
            fields.append("error = ?")
            params.append(error)
        if not fields:
            return
        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(job_id)
        with self._conn() as conn:
            conn.execute(f"UPDATE downloads SET {', '.join(fields)} WHERE id = ?", params)

