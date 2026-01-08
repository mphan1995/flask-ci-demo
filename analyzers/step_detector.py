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
    ("kubectl apply", re.compile(r"\bkubectl\s+apply\b", re.IGNORECASE)),
    ("kubectl rollout", re.compile(r"\bkubectl\s+rollout\s+status\b", re.IGNORECASE)),
    ("terraform init", re.compile(r"\bterraform\s+init\b", re.IGNORECASE)),
    ("terraform plan", re.compile(r"\bterraform\s+plan\b", re.IGNORECASE)),
    ("terraform apply", re.compile(r"\bterraform\s+apply\b", re.IGNORECASE)),
    ("ansible-playbook", re.compile(r"\bansible-playbook\b", re.IGNORECASE)),
    ("git clone", re.compile(r"\bgit\s+clone\b", re.IGNORECASE)),
    ("git fetch", re.compile(r"\bgit\s+fetch\b", re.IGNORECASE)),
    ("git pull", re.compile(r"\bgit\s+pull\b", re.IGNORECASE)),
    ("git push", re.compile(r"\bgit\s+push\b", re.IGNORECASE)),
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
