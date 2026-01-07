from dataclasses import dataclass
from typing import Optional


@dataclass
class PipelineEvent:
    """
    Represents a normalized CI/CD pipeline event
    extracted from raw pipeline logs.
    """

    timestamp: Optional[str]        # ISO or raw timestamp if available
    pipeline_name: Optional[str]    # Jenkins job / workflow name
    stage_name: Optional[str]       # Build / Test / Deploy (chuẩn 3 stages)
    step_name: Optional[str]        # Shell / Maven / Docker
    log_level: str                  # INFO | WARNING | ERROR
    message: str                    # Raw log line (cleaned)
    raw_line: str                   # Original unmodified log line
    source: str                     # jenkins | github | gitlab
