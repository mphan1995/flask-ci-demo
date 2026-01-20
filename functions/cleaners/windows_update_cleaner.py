import re

from ..security import is_admin, is_windows, run_cmd, run_powershell


def _parse_cleanup_size(text):
    match = re.search(r"Size of Cleanup\s*:\s*([0-9\.]+)\s*([A-Za-z]+)", text)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).upper()
    scale = {
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
    }.get(unit)
    if not scale:
        return None
    return int(value * scale)


def scan_windows_update():
    if not is_windows():
        return {"ok": False, "error": "windows_only"}
    if not is_admin():
        return {"ok": False, "error": "admin_required"}

    result = run_cmd(
        ["Dism.exe", "/Online", "/Cleanup-Image", "/AnalyzeComponentStore"],
        timeout=600,
    )
    estimated = _parse_cleanup_size(result.get("stdout", ""))
    return {
        "ok": result["ok"],
        "estimated_bytes": estimated,
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "returncode": result.get("returncode", -1),
    }


def run_windows_update(dry_run=False):
    if not is_windows():
        return {"ok": False, "error": "windows_only"}
    if not is_admin():
        return {"ok": False, "error": "admin_required"}

    if dry_run:
        result = scan_windows_update()
        result["dry_run"] = True
        return result

    cleanup = run_cmd(
        ["Dism.exe", "/Online", "/Cleanup-Image", "/StartComponentCleanup"],
        timeout=1800,
    )
    delivery = run_powershell("Clear-DODownloadCache -Force -ErrorAction SilentlyContinue")

    return {
        "ok": cleanup.get("ok", False) and delivery.get("ok", False),
        "dism": cleanup,
        "delivery_optimization": delivery,
    }
