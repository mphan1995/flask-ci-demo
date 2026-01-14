from __future__ import annotations

import json
import re
from pathlib import Path

RULE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


REQUIRED_FIELDS = {"id", "title", "risk", "type", "targets", "detect", "apply", "rollback"}


def load_rules(rules_path: Path) -> dict:
    with rules_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    rules = data.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("rules must be a list")

    seen = set()
    for rule in rules:
        if not REQUIRED_FIELDS.issubset(rule.keys()):
            missing = REQUIRED_FIELDS - set(rule.keys())
            raise ValueError(f"rule missing fields: {', '.join(sorted(missing))}")
        if not RULE_ID_RE.match(rule.get("id", "")):
            raise ValueError(f"invalid rule id: {rule.get('id')}")
        if rule["id"] in seen:
            raise ValueError(f"duplicate rule id: {rule['id']}")
        seen.add(rule["id"])

    return data


def validate_selected_ids(selected: list, rules: list[dict]) -> list[str]:
    if not isinstance(selected, list):
        raise ValueError("selected_actions must be a list")

    valid_ids = {rule["id"] for rule in rules}
    clean = []
    for item in selected:
        if not isinstance(item, str):
            raise ValueError("selected_actions must contain strings")
        if not RULE_ID_RE.match(item):
            raise ValueError(f"invalid rule id: {item}")
        if item not in valid_ids:
            raise ValueError(f"unknown rule id: {item}")
        if item not in clean:
            clean.append(item)
    return clean
