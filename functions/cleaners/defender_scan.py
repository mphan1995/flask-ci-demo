from ..security import is_windows, run_powershell


def scan_defender():
    if not is_windows():
        return {"ok": False, "error": "windows_only"}
    result = run_powershell("Get-MpComputerStatus")
    return {
        "ok": result.get("ok", False),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "returncode": result.get("returncode", -1),
    }


def run_defender(dry_run=False):
    if not is_windows():
        return {"ok": False, "error": "windows_only"}
    if dry_run:
        return {"ok": True, "dry_run": True, "notes": "Quick scan skipped in dry run."}
    result = run_powershell("Start-MpScan -ScanType QuickScan")
    return {
        "ok": result.get("ok", False),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "returncode": result.get("returncode", -1),
    }
