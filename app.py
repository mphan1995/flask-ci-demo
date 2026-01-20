import argparse
import os
import socket
import time

from flask import Flask, jsonify, render_template, request

from functions.action_registry import get_action, list_actions
from functions.disk_info import get_drives, get_top_folders
from functions.logging_utils import append_log, read_logs
from functions.security import (
    SIMULATION_MODE,
    current_user,
    is_admin,
    job_lock,
    launch_admin_instance,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
DEFAULT_ADMIN_PORT = int(os.getenv("ADMIN_PORT", "5001"))


def _action_response(action, mode, result, started_at, ended_at, dry_run=False):
    return {
        "action_id": action["id"],
        "action_name": action["name"],
        "mode": mode,
        "ok": bool(result.get("ok")),
        "dry_run": dry_run,
        "simulation": SIMULATION_MODE,
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_ms": int((ended_at - started_at) * 1000),
        "result": result,
    }


def _log_action(action, mode, result, started_at, ended_at, dry_run=False):
    entry = {
        "action_id": action["id"],
        "action_name": action["name"],
        "mode": mode,
        "status": "success" if result.get("ok") else "error",
        "user": current_user(),
        "dry_run": dry_run,
        "duration_ms": int((ended_at - started_at) * 1000),
        "bytes": result.get("bytes") or result.get("estimated_bytes"),
        "errors": result.get("errors"),
    }
    append_log(entry)


def _is_port_open(host, port, timeout=0.2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/actions")
def actions():
    return render_template("actions.html")


@app.route("/logs")
def logs():
    return render_template("logs.html")


@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(
        {
            "ok": True,
            "simulation": SIMULATION_MODE,
            "busy": job_lock.is_locked(),
            "admin": is_admin(),
        }
    )


@app.route("/api/actions", methods=["GET"])
def api_actions():
    return jsonify({"ok": True, "actions": list_actions()})


@app.route("/api/drives", methods=["GET"])
def api_drives():
    return jsonify(
        {
            "ok": True,
            "drives": get_drives(),
            "top_folders": get_top_folders(),
        }
    )


@app.route("/api/actions/<action_id>/scan", methods=["POST"])
def api_action_scan(action_id):
    action = get_action(action_id)
    if not action:
        return jsonify({"ok": False, "error": "action_not_found"}), 404
    if job_lock.is_locked():
        return jsonify({"ok": False, "error": "job_in_progress"}), 409

    started_at = time.time()
    result = action["scan"]()
    ended_at = time.time()

    response = _action_response(action, "scan", result, started_at, ended_at, dry_run=True)
    _log_action(action, "scan", result, started_at, ended_at, dry_run=True)
    return jsonify(response)


@app.route("/api/actions/<action_id>/run", methods=["POST"])
def api_action_run(action_id):
    action = get_action(action_id)
    if not action:
        return jsonify({"ok": False, "error": "action_not_found"}), 404

    payload = request.get_json(silent=True) or {}
    confirm = payload.get("confirm") is True
    dry_run = payload.get("dry_run") is True or SIMULATION_MODE

    if not confirm:
        return jsonify({"ok": False, "error": "confirmation_required"}), 400

    if not job_lock.acquire():
        return jsonify({"ok": False, "error": "job_in_progress"}), 409

    started_at = time.time()
    try:
        result = action["run"](dry_run=dry_run)
    finally:
        job_lock.release()
    ended_at = time.time()

    response = _action_response(action, "run", result, started_at, ended_at, dry_run=dry_run)
    _log_action(action, "run", result, started_at, ended_at, dry_run=dry_run)
    return jsonify(response)


@app.route("/api/logs", methods=["GET"])
def api_logs():
    limit = request.args.get("limit", "200")
    try:
        limit = max(1, min(1000, int(limit)))
    except ValueError:
        limit = 200
    return jsonify({"ok": True, "logs": read_logs(limit=limit)})


@app.route("/api/admin/launch", methods=["POST"])
def api_admin_launch():
    admin_port = DEFAULT_ADMIN_PORT
    admin_url = f"http://127.0.0.1:{admin_port}"
    if is_admin():
        return jsonify({"ok": True, "already_admin": True, "url": admin_url})

    if _is_port_open("127.0.0.1", admin_port):
        return jsonify({"ok": True, "already_running": True, "url": admin_url})

    result = launch_admin_instance(admin_port)
    result["url"] = admin_url
    return jsonify(result)


def _parse_args():
    parser = argparse.ArgumentParser(description="Windows Disk Cleaner Dashboard")
    parser.add_argument("--host", default=os.getenv("APP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("APP_PORT", "5000")))
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    app.config["APP_PORT"] = args.port
    app.run(host=args.host, port=args.port, debug=args.debug)
