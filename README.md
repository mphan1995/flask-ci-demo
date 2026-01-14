# MAX_ENGINE_WIN11

Local-only Flask app for safe Windows 11 optimization. Default mode is read-only (scan + plan). Apply only runs when the user clicks Apply and runs with Administrator privileges.

## Features

- Dry-run by default (no changes)  -- DON'T USE.
- Backup + rollback for services, scheduled tasks, and registry values
- JSON + text logs for every run
- Skip core services (Windows Update, Defender core, networking, RPC, WMI)
- Full scan of running services (read-only) before enabling actions
- Idempotent operations (safe to re-apply)

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:5050

Extra pages:

- `/list` for the full service ledger
- `/check` for local verification of targeted services
- `/processes` for memory-heavy apps and related service hints

## Run elevated (Administrator)

Apply and rollback require Administrator rights. The app auto-requests elevation when started on Windows (UAC prompt). If you cancel, the app exits.

Manual option:

1. Search "Windows Terminal"
2. Right click and choose "Run as administrator"
3. Activate the venv and run `python app.py`

The UI shows an Admin status badge.

## API

- `GET /api/health`
- `GET /api/scan`
- `POST /api/apply` body: `{ "selected_actions": ["rule_id"], "mode": "dry_run|apply", "action": "disable|enable" }`
- `POST /api/rollback` body: `{ "rollback_id": "<backup_id>" }`
- `GET /api/history`
- `GET /api/logs/<id>`
- `GET /api/services`
- `GET /api/processes`

## Data paths

- Backups: `scripts/data/backup/<backup_id>/backup.json`
- Logs: `scripts/data/logs/`

## Rule engine

Rules live in `config/rules.default.json` and are grouped by category. Each rule defines:

- `type`: registry | service | task
- `targets`: list of targets
- `detect`: state that counts as "disabled"
- `apply`: desired state
- `rollback`: restore from backup

Add a new rule by appending an entry that follows the same schema and reload the app.

## Safety notes

- No file deletions.
- Core services are not targeted.
- Always run a scan and dry-run plan before apply.
- Rollback uses the backup id from the apply summary.

## Development

This project does not use a database. All state is stored in the filesystem for local use.
