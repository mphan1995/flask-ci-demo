from dataclasses import dataclass
import re
from typing import Optional

@dataclass
class StepMatch:
    label: str
    start_line: str


STEP_PATTERNS = [
    ("pip install", re.compile(r"\b(?:python\s+-m\s+)?pip\s+install\b", re.IGNORECASE)),
    ("docker build", re.compile(r"\bdocker\s+(?:buildx\s+build|build)\b", re.IGNORECASE)),
    ("helm upgrade", re.compile(r"\bhelm\s+upgrade\b", re.IGNORECASE)),
]


def detect_step_start(line: str) -> Optional[StepMatch]:
    normalized = line.strip()
    if not normalized:
        return None

    for label, pattern in STEP_PATTERNS:
        if pattern.search(normalized):
            return StepMatch(label=label, start_line=normalized)

    return None


def detect_step(line: str) -> Optional[StepMatch]:
    return detect_step_start(line)
