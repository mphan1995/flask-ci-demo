import os
import tempfile

from ..security import (
    DEFAULT_EXCLUSIONS,
    get_dir_size,
    is_admin,
    is_windows,
    safe_delete_contents,
)


def _scan_path(label, path):
    if not path or not os.path.exists(path):
        return {
            "ok": True,
            "label": label,
            "path": path or "",
            "bytes": 0,
            "files": 0,
            "truncated": False,
            "notes": "path_not_found",
        }
    size_info = get_dir_size(
        path,
        exclusions=DEFAULT_EXCLUSIONS,
        max_files=200000,
        max_depth=8,
    )
    return {
        "ok": True,
        "label": label,
        "path": path,
        "bytes": size_info["bytes"],
        "files": size_info["files"],
        "truncated": size_info["truncated"],
        "errors": size_info["errors"],
    }


def _run_path(label, path, allowed_roots, dry_run=False):
    if not path or not os.path.exists(path):
        return {
            "ok": True,
            "label": label,
            "path": path or "",
            "bytes": 0,
            "files_deleted": 0,
            "notes": "path_not_found",
            "dry_run": dry_run,
        }
    result = safe_delete_contents(
        path,
        allowed_roots=allowed_roots,
        dry_run=dry_run,
        exclusions=DEFAULT_EXCLUSIONS,
        max_files=200000,
    )
    result.update(
        {
            "label": label,
            "path": path,
            "dry_run": dry_run,
        }
    )
    return result


def scan_user_temp():
    path = tempfile.gettempdir()
    return _scan_path("User TEMP", path)


def run_user_temp(dry_run=False):
    path = tempfile.gettempdir()
    return _run_path("User TEMP", path, allowed_roots=[path], dry_run=dry_run)


def scan_windows_temp():
    if not is_windows():
        return {"ok": False, "error": "windows_only"}
    if not is_admin():
        return {"ok": False, "error": "admin_required"}
    windir = os.getenv("WINDIR", "C:\\Windows")
    path = os.path.join(windir, "Temp")
    return _scan_path("Windows TEMP", path)


def run_windows_temp(dry_run=False):
    if not is_windows():
        return {"ok": False, "error": "windows_only"}
    if not is_admin():
        return {"ok": False, "error": "admin_required"}
    windir = os.getenv("WINDIR", "C:\\Windows")
    path = os.path.join(windir, "Temp")
    return _run_path("Windows TEMP", path, allowed_roots=[path], dry_run=dry_run)
