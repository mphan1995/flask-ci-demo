# Windows Disk Cleaner Dashboard

Local-only Flask dashboard to scan and clean common Windows disk clutter with strict safety guardrails. The service runs on `127.0.0.1` and exposes a minimal allowlist of actions. No arbitrary command execution is permitted.

## Features
- Dashboard with drive usage and safe top-folder sampling (user profile only)
- Allowlisted cleanup modules with Scan -> Preview -> Execute flow
- Dry-run/estimate for each module
- Concurrency lock (one cleanup job at a time)
- Detailed audit logs and JSON responses

## Safety Checklist
- Allowlist actions only (no user-supplied commands)
- Path validation and traversal protection
- Default SAFE_MODE blocks WinSxS, System32, and Program Files paths
- Dry-run support and global SIMULATION mode
- Exclusion patterns for risky or locked file types
- Browser cache cleanup only when browser processes are closed
- Audit log recorded for every scan/run

## Requirements
- Windows 10/11
- Python 3.10+
- PowerShell available in PATH

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## Run as Administrator (for admin actions)
Some modules require elevation (Windows Temp, Windows Update cleanup). Launch PowerShell or Command Prompt as Administrator, then run:
```bash
python app.py
```

## Configuration
- `SIMULATION=1` forces run actions into dry-run mode (no deletion)
- `SAFE_MODE=1` (default) blocks risky system paths

Example:
```bash
set SIMULATION=1
python app.py
```

## API Endpoints
- `GET /api/status` - service status and privilege mode
- `GET /api/drives` - drive usage and top folders
- `GET /api/actions` - list allowlisted actions
- `POST /api/actions/<action_id>/scan` - scan/estimate action
- `POST /api/actions/<action_id>/run` - execute action (requires `{ "confirm": true }`)
- `GET /api/logs` - recent audit logs

## Logs
Logs are stored at `data/logs.jsonl` in JSON Lines format. Each record contains action metadata, timestamps, duration, and bytes (when available).

## Notes and Limitations
- Windows Update cleanup uses DISM and may take several minutes.
- Delivery Optimization cleanup uses `Clear-DODownloadCache` if available.
- Cache sizes are best-effort estimates; locked files may be skipped.
- This tool is intended for personal, local use only.

## Tests
```bash
pytest -q
```
