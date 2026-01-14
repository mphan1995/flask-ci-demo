from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from functions.rules_loader import load_rules, validate_selected_ids
from functions.shell_runner import is_admin, run_powershell
from functions.state_store import list_backups, list_logs, read_log

BASE_DIR = Path(__file__).resolve().parent
RULES_PATH = BASE_DIR / "config" / "rules.default.json"
PS_DIR = BASE_DIR / "scripts" / "ps"
DATA_DIR = BASE_DIR / "scripts" / "data"
LOG_DIR = DATA_DIR / "logs"
BACKUP_DIR = DATA_DIR / "backup"

app = Flask(__name__)

RISK_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def build_service_rule_map(rules: list[dict]) -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    for rule in rules:
        if rule.get("type") != "service":
            continue
        for target in rule.get("targets", []):
            name = target.get("name")
            if not name:
                continue
            entry = mapping.setdefault(
                name,
                {"rule_ids": [], "notes": [], "risk": None, "groups": []},
            )
            entry["rule_ids"].append(rule["id"])
            if rule.get("notes"):
                entry["notes"].append(rule["notes"])
            if rule.get("group"):
                entry["groups"].append(rule.get("group"))
            risk = rule.get("risk")
            if risk and (
                entry["risk"] is None
                or RISK_ORDER.get(risk, 0) > RISK_ORDER.get(entry["risk"], 0)
            ):
                entry["risk"] = risk

    for entry in mapping.values():
        entry["rule_ids"] = sorted(set(entry["rule_ids"]))
        entry["groups"] = sorted({g for g in entry["groups"] if g})
        entry["notes"] = " / ".join(sorted(set(entry["notes"])))
    return mapping


def json_error(message: str, status: int = 400, details: dict | None = None):
    payload = {"ok": False, "error": {"message": message}}
    if details:
        payload["error"]["details"] = details
    return jsonify(payload), status


def ensure_admin() -> str:
    if os.name != "nt":
        return "non_windows"
    if is_admin():
        return "admin"
    if "--elevated" in sys.argv:
        return "failed"
    try:
        import ctypes  # pylint: disable=import-outside-toplevel

        params = " ".join([f'"{arg}"' for arg in sys.argv] + ["--elevated"])
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            params,
            None,
            1,
        )
    except Exception:
        return "failed"

    if result <= 32:
        return "failed"
    return "launched"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/check")
def check():
    return render_template("check.html")


@app.get("/list")
def list_services():
    return render_template("list.html")


@app.get("/processes")
def processes():
    return render_template("processes.html")


@app.get("/api/health")
def api_health():
    return jsonify(
        {
            "ok": True,
            "admin": is_admin(),
            "platform": platform.system(),
            "release": platform.release(),
            "rules_path": str(RULES_PATH),
        }
    )


@app.get("/api/scan")
def api_scan():
    script_path = PS_DIR / "scan.ps1"
    result = run_powershell(
        script_path,
        args=[("RulesPath", str(RULES_PATH))],
        timeout=120,
        log_root=LOG_DIR,
    )
    if not result["ok"]:
        return json_error("scan failed", status=500, details=result["error"])
    return jsonify(result["data"])


@app.get("/api/services")
def api_services():
    script_path = PS_DIR / "services.ps1"
    result = run_powershell(
        script_path,
        args=[],
        timeout=120,
        log_root=LOG_DIR,
    )
    if not result["ok"]:
        return json_error("services scan failed", status=500, details=result["error"])

    data = result["data"]
    if not data.get("ok", True):
        return json_error("services scan failed", status=500, details=data)

    try:
        rules = load_rules(RULES_PATH)["rules"]
    except Exception as exc:
        return json_error("failed to load rules", status=500, details={"error": str(exc)})

    service_map = build_service_rule_map(rules)
    services = data.get("services", [])
    for service in services:
        meta = service_map.get(service.get("name"))
        if meta:
            service["rule_ids"] = meta["rule_ids"]
            service["notes"] = meta["notes"]
            service["risk"] = meta["risk"]
            service["groups"] = meta["groups"]
        else:
            service["rule_ids"] = []
            service["notes"] = ""
            service["risk"] = None
            service["groups"] = []

    data["rules_loaded"] = len(rules)
    data["services"] = services
    return jsonify(data)


@app.get("/api/processes")
def api_processes():
    script_path = PS_DIR / "processes.ps1"
    result = run_powershell(
        script_path,
        args=[],
        timeout=120,
        log_root=LOG_DIR,
    )
    if not result["ok"]:
        return json_error("process scan failed", status=500, details=result["error"])

    data = result["data"]
    if not data.get("ok", True):
        return json_error("process scan failed", status=500, details=data)

    processes = data.get("processes", [])
    services = data.get("services", [])

    try:
        rules = load_rules(RULES_PATH)["rules"]
    except Exception as exc:
        return json_error("failed to load rules", status=500, details={"error": str(exc)})

    service_map = build_service_rule_map(rules)
    rule_index = {
        rule["id"]: {
            "id": rule["id"],
            "title": rule.get("title"),
            "risk": rule.get("risk"),
            "group": rule.get("group"),
        }
        for rule in rules
    }

    services_by_pid: dict[int, list[dict]] = {}
    for service in services:
        pid = service.get("pid")
        name = service.get("name")
        if pid is None or not name:
            continue
        entry = {
            "name": name,
            "display_name": service.get("display_name") or name,
            "state": service.get("state") or "Unknown",
            "start_mode": service.get("start_mode") or None,
            "pid": pid,
        }
        meta = service_map.get(name)
        if meta:
            entry["rule_ids"] = meta["rule_ids"]
            entry["notes"] = meta["notes"]
            entry["risk"] = meta["risk"]
            entry["groups"] = meta["groups"]
            entry["rules"] = [
                rule_index[rule_id]
                for rule_id in meta["rule_ids"]
                if rule_id in rule_index
            ]
        else:
            entry["rule_ids"] = []
            entry["notes"] = ""
            entry["risk"] = None
            entry["groups"] = []
            entry["rules"] = []
        services_by_pid.setdefault(pid, []).append(entry)

    groups: dict[str, dict] = {}
    for proc in processes:
        name = proc.get("name") or "Unknown"
        key = name.lower()
        entry = groups.setdefault(
            key,
            {
                "name": name,
                "process_count": 0,
                "memory_bytes": 0,
                "pids": [],
            },
        )
        entry["process_count"] += 1
        memory = proc.get("working_set") or 0
        try:
            memory_value = int(memory)
        except (TypeError, ValueError):
            memory_value = 0
        entry["memory_bytes"] += memory_value
        pid = proc.get("pid")
        if pid is not None:
            entry["pids"].append(pid)

    groups_out = []
    for entry in groups.values():
        services_map: dict[str, dict] = {}
        for pid in entry["pids"]:
            for svc in services_by_pid.get(pid, []):
                services_map[svc["name"]] = svc
        services_list = sorted(
            services_map.values(),
            key=lambda item: (item.get("display_name") or item["name"]).lower(),
        )
        entry["services"] = services_list
        entry["services_count"] = len(services_list)
        entry["memory_mb"] = round(entry["memory_bytes"] / (1024 * 1024), 1)
        groups_out.append(entry)

    groups_out.sort(key=lambda item: item["memory_bytes"], reverse=True)

    summary = {
        "processes": len(processes),
        "groups": len(groups_out),
        "services": len(services),
        "process_source": data.get("process_source"),
        "service_source": data.get("service_source"),
    }

    return jsonify(
        {
            "ok": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "process_groups": groups_out,
            "rules_loaded": len(rules),
        }
    )


@app.post("/api/apply")
def api_apply():
    payload = request.get_json(silent=True) or {}
    selected = payload.get("selected_actions", [])
    mode = payload.get("mode", "dry_run")
    action = payload.get("action", "disable")

    if mode not in {"dry_run", "apply"}:
        return json_error("mode must be dry_run or apply")
    if action not in {"disable", "enable"}:
        return json_error("action must be disable or enable")

    try:
        rules = load_rules(RULES_PATH)["rules"]
    except Exception as exc:
        return json_error("failed to load rules", status=500, details={"error": str(exc)})

    try:
        selected_ids = validate_selected_ids(selected, rules)
    except ValueError as exc:
        return json_error(str(exc))

    if not selected_ids:
        return json_error("no selected actions")

    if mode == "apply" and not is_admin():
        return json_error("admin privileges required for apply", status=403)

    script_path = PS_DIR / "apply.ps1"
    result = run_powershell(
        script_path,
        args=[
            ("RulesPath", str(RULES_PATH)),
            ("SelectedIds", ",".join(selected_ids)),
            ("Mode", mode),
            ("Action", action),
        ],
        timeout=240,
        log_root=LOG_DIR,
    )
    if not result["ok"]:
        return json_error("apply failed", status=500, details=result["error"])
    return jsonify(result["data"])


@app.post("/api/rollback")
def api_rollback():
    payload = request.get_json(silent=True) or {}
    rollback_id = payload.get("rollback_id")
    if not rollback_id:
        return json_error("rollback_id is required")

    if not is_admin():
        return json_error("admin privileges required for rollback", status=403)

    script_path = PS_DIR / "rollback.ps1"
    result = run_powershell(
        script_path,
        args=[("BackupId", str(rollback_id))],
        timeout=240,
        log_root=LOG_DIR,
    )
    if not result["ok"]:
        return json_error("rollback failed", status=500, details=result["error"])
    return jsonify(result["data"])


@app.get("/api/history")
def api_history():
    backups = list_backups(BACKUP_DIR, limit=30)
    logs = list_logs(LOG_DIR, limit=50)
    return jsonify({"ok": True, "backups": backups, "logs": logs})


@app.get("/api/logs/<log_id>")
def api_logs(log_id: str):
    log_data = read_log(LOG_DIR, log_id)
    if not log_data:
        return json_error("log not found", status=404)
    return jsonify({"ok": True, "log": log_data})


if __name__ == "__main__":
    status = ensure_admin()
    if status == "failed":
        print("Administrator privileges are required to run this app.")
        sys.exit(1)
    if status == "launched":
        sys.exit(0)
    app.run(host="127.0.0.1", port=5050, debug=False)
