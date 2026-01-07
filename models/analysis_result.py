from dataclasses import dataclass
from typing import List


@dataclass
class AnalysisResult:
    root_cause: str
    confidence: float
    evidence: List[str]
