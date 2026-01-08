from dataclasses import dataclass
from typing import Optional


@dataclass
class PipelineEvent:
    """
    Represents a normalized CI/CD pipeline event
    extracted from raw pipeline logs.
    """

    # Identification
    pipeline_name: Optional[str]
    build_id: Optional[str]        # Jenkins build number / run id

    # Context
    stage_name: Optional[str]
    step_name: Optional[str]
    origin_step: Optional[str]

    # Log details
    timestamp: Optional[str]
    log_level: str                 # INFO | WARNING | ERROR
    message: str                   # Cleaned message
    raw_line: str                  # Original log line

    # Source
    source: str                    # jenkins | github | gitlab
