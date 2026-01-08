from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AnalysisResult:
    root_cause: str
    confidence: float
    evidence: List[str]
    origin_step: Optional[str] = None
    failure_surface: Optional[str] = None
