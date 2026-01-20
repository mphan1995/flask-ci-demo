import time

from flask import Flask, jsonify, render_template, request

from functions.action_registry import get_action, list_actions
from functions.disk_info import get_drives, get_top_folders
from functions.logging_utils import append_log, read_logs
from functions.security import SIMULATION_MODE, current_user, is_admin, job_lock

app = Flask(__name__, template_folder="templates", static_folder="static")


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
