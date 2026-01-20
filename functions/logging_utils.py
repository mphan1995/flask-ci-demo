import json
import os
from datetime import datetime

from .security import DATA_DIR

LOG_FILE = os.path.join(DATA_DIR, "logs.jsonl")


def _ensure_log_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as _:
            pass


def append_log(entry):
    _ensure_log_file()
    payload = dict(entry)
    payload["timestamp"] = datetime.utcnow().isoformat() + "Z"
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def read_logs(limit=200):
    _ensure_log_file()
    with open(LOG_FILE, "r", encoding="utf-8") as handle:
        lines = handle.readlines()
    entries = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries
