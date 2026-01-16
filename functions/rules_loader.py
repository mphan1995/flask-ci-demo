from __future__ import annotations

import json
import re
from pathlib import Path

RULE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


REQUIRED_FIELDS = {"id", "title", "risk", "type", "targets", "detect", "apply", "rollback"}


def _merge_groups(base_groups: list, extra_groups: list) -> list:
    merged = []
    seen = set()
    for group in base_groups + extra_groups:
        if not isinstance(group, dict):
            continue
        group_id = group.get("id")
        if not group_id or group_id in seen:
            continue
        merged.append(group)
        seen.add(group_id)
    return merged


def load_rules(rules_path: Path, detected_path: Path | None = None) -> dict:
    with rules_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    rules = data.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("rules must be a list")

    groups = data.get("groups", [])
    if not isinstance(groups, list):
        groups = []

    extra_rules = []
    extra_groups = []
    if detected_path and detected_path.exists():
        try:
            extra_data = json.loads(detected_path.read_text(encoding="utf-8"))
            extra_rules = extra_data.get("rules", [])
            extra_groups = extra_data.get("groups", [])
        except Exception:
            extra_rules = []
            extra_groups = []

    if isinstance(extra_rules, list) and extra_rules:
        rules = rules + extra_rules
    if isinstance(extra_groups, list) and extra_groups:
        data["groups"] = _merge_groups(groups, extra_groups)
    else:
        data["groups"] = groups

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

    data["rules"] = rules
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
