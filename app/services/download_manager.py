from __future__ import annotations

import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import requests

from app.models import DownloadJob


class DownloadManager:
    def __init__(self, storage, event_bus=None, library=None, max_workers: int = 2):
        self.storage = storage
        self.event_bus = event_bus
        self.library = library
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def enqueue(self, url: str, mode: str, target_dir: Path, max_size_mb: int) -> int:
        job = DownloadJob(
            id=None,
            url=url,
            mode=mode,
            status="queued",
            progress=0.0,
            local_path=None,
            error=None,
        )
        job_id = self.storage.create_download(job)
        self.executor.submit(self._download, job_id, url, target_dir, max_size_mb)
        return job_id

    def _emit(self, payload):
        if self.event_bus:
            self.event_bus.publish("download", payload)

    def _download(self, job_id: int, url: str, target_dir: Path, max_size_mb: int):
        target_dir.mkdir(parents=True, exist_ok=True)
        self.storage.update_download(job_id, status="downloading", progress=0.0)
        self._emit({"id": job_id, "status": "downloading", "progress": 0})

        try:
            with requests.get(url, stream=True, timeout=15) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                max_bytes = max_size_mb * 1024 * 1024
                if total and total > max_bytes:
                    raise ValueError("File too large")

                filename = self._infer_filename(url, r.headers.get("Content-Disposition"))
                dest_path = target_dir / filename
                downloaded = 0

                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        if downloaded > max_bytes:
                            raise ValueError("File exceeded size limit")
                        progress = (downloaded / total * 100) if total else 0
                        self.storage.update_download(job_id, progress=progress)
                        self._emit({"id": job_id, "status": "downloading", "progress": progress})

            self.storage.update_download(job_id, status="done", progress=100, local_path=str(dest_path))
            if self.library:
                try:
                    self.library.add_local_file(dest_path)
                except Exception:
                    pass
            self._emit({"id": job_id, "status": "done", "progress": 100})
        except Exception as exc:  # noqa: BLE001
            self.storage.update_download(job_id, status="failed", error=str(exc))
            self._emit({"id": job_id, "status": "failed", "error": str(exc)})

    @staticmethod
    def _infer_filename(url: str, content_disposition: Optional[str]) -> str:
        if content_disposition and "filename=" in content_disposition:
            return content_disposition.split("filename=")[-1].strip('"')
        name = os.path.basename(url.split("?")[0]) or f"track-{int(time.time())}.bin"
        return name

    def cleanup_cache(self, cache_dir: Path, ttl_hours: int, max_gb: int):
        # TODO: implement TTL + size-based cleanup
        _ = cache_dir, ttl_hours, max_gb
