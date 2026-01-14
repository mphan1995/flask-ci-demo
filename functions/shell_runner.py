from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

RULE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def is_admin() -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes  # pylint: disable=import-outside-toplevel

        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _timestamp_id(prefix: str) -> str:
    return f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"


def _find_powershell() -> str | None:
    for exe in ("powershell.exe", "pwsh", "powershell"):
        path = shutil.which(exe)
        if path:
            return path
    return None


def _write_runner_logs(log_root: Path, log_id: str, payload: dict) -> None:
    log_root.mkdir(parents=True, exist_ok=True)
    json_path = log_root / f"{log_id}.json"
    text_path = log_root / f"{log_id}.log"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    lines = [
        f"time: {payload.get('ended_at')}",
        f"command: {' '.join(payload.get('command', []))}",
        f"exit_code: {payload.get('exit_code')}",
        "stdout:",
        payload.get("stdout", ""),
        "stderr:",
        payload.get("stderr", ""),
    ]
    text_path.write_text("\n".join(lines), encoding="utf-8")


def run_powershell(
    script_path: Path,
    args: list[tuple[str, str]],
    timeout: int = 120,
    log_root: Path | None = None,
) -> dict:
    ps = _find_powershell()
    if not ps:
        return {
            "ok": False,
            "error": {"message": "powershell not found"},
        }

    if not script_path.exists():
        return {
            "ok": False,
            "error": {"message": f"script not found: {script_path}"},
        }

    command = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
    for key, value in args:
        if isinstance(value, str) and ("\n" in value or "\r" in value):
            return {
                "ok": False,
                "error": {"message": f"invalid argument for {key}"},
            }
        command.extend([f"-{key}", str(value)])

    log_id = _timestamp_id("runner")
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": {"message": "powershell timed out"},
        }

    ended_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    payload = {
        "started_at": started_at,
        "ended_at": ended_at,
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }

    if log_root:
        _write_runner_logs(log_root, log_id, payload)

    if proc.returncode != 0:
        return {
            "ok": False,
            "error": {
                "message": "powershell failed",
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
                "log_id": log_id,
            },
        }

    stdout = proc.stdout.strip()
    if not stdout:
        return {
            "ok": False,
            "error": {
                "message": "empty output from powershell",
                "log_id": log_id,
            },
        }

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "error": {
                "message": "invalid json output",
                "detail": str(exc),
                "stdout": stdout,
                "log_id": log_id,
            },
        }

    return {"ok": True, "data": data, "log_id": log_id}
