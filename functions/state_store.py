from __future__ import annotations

import json
import re
from pathlib import Path

LOG_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _safe_stat(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def list_backups(backup_root: Path, limit: int = 20) -> list[dict]:
    items = []
    if not backup_root.exists():
        return items

    for entry in backup_root.iterdir():
        if not entry.is_dir():
            continue
        backup_file = entry / "backup.json"
        meta = {"id": entry.name, "mtime": _safe_stat(entry)}
        if backup_file.exists():
            try:
                data = json.loads(backup_file.read_text(encoding="utf-8"))
                meta["created_at"] = data.get("created_at")
                meta["rules"] = data.get("rules", [])
            except Exception:
                meta["created_at"] = None
        items.append(meta)

    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items[:limit]


def list_logs(log_root: Path, limit: int = 50) -> list[dict]:
    items_map: dict[str, dict] = {}
    if not log_root.exists():
        return []

    for entry in log_root.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix not in {".json", ".log"}:
            continue
        key = entry.stem
        if key not in items_map:
            items_map[key] = {
                "id": key,
                "files": [],
                "formats": [],
                "mtime": _safe_stat(entry),
                "size": 0,
            }
        items_map[key]["files"].append(entry.name)
        items_map[key]["formats"].append(entry.suffix.lstrip("."))
        items_map[key]["mtime"] = max(items_map[key]["mtime"], _safe_stat(entry))
        items_map[key]["size"] += entry.stat().st_size

    items = list(items_map.values())
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items[:limit]


def read_log(log_root: Path, log_id: str) -> dict | None:
    if not LOG_ID_RE.match(log_id):
        return None

    json_path = log_root / f"{log_id}.json"
    text_path = log_root / f"{log_id}.log"

    if not json_path.exists() and not text_path.exists():
        return None

    payload = {"id": log_id}
    if json_path.exists():
        try:
            payload["json"] = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            payload["json"] = json_path.read_text(encoding="utf-8")

    if text_path.exists():
        payload["text"] = text_path.read_text(encoding="utf-8")

    return payload
