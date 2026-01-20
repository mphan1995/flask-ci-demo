import os

from ..disk_info import get_drives
from ..security import DEFAULT_EXCLUSIONS, get_dir_size, is_windows, run_powershell


def _recycle_bin_paths():
    paths = []
    for drive in get_drives():
        root = drive["name"]
        path = os.path.join(root, "$Recycle.Bin")
        if os.path.exists(path):
            paths.append(path)
    return paths


def scan():
    if not is_windows():
        return {"ok": False, "error": "windows_only"}

    total = 0
    items = []
    errors = []

    for path in _recycle_bin_paths():
        size_info = get_dir_size(
            path,
            exclusions=DEFAULT_EXCLUSIONS,
            max_files=200000,
            max_depth=10,
        )
        total += size_info["bytes"]
        items.append(
            {
                "path": path,
                "bytes": size_info["bytes"],
                "files": size_info["files"],
                "truncated": size_info["truncated"],
            }
        )
        errors.extend(size_info["errors"])

    return {
        "ok": True,
        "bytes": total,
        "items": items,
        "errors": errors,
    }


def run(dry_run=False):
    estimate = scan()
    if not estimate.get("ok"):
        return estimate
    if dry_run:
        estimate["dry_run"] = True
        return estimate

    result = run_powershell("Clear-RecycleBin -Force -ErrorAction SilentlyContinue")
    return {
        "ok": result["ok"],
        "estimated_bytes": estimate.get("bytes", 0),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "returncode": result.get("returncode", -1),
    }
