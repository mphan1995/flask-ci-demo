from dataclasses import dataclass
import re
from typing import Optional

from analyzers.knowledge_base import STEP_KNOWLEDGE


@dataclass
class StepMatch:
    label: str
    start_line: str


STEP_PATTERNS = [
    (step.label, re.compile(step.pattern, re.IGNORECASE))
    for step in STEP_KNOWLEDGE
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
