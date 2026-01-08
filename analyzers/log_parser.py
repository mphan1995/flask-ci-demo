import re
from typing import List
from models.pipeline_event import PipelineEvent
from analyzers.step_detector import detect_step_start


STAGE_PATTERN = re.compile(r"\[Pipeline\]\s+stage\s+\((.+?)\)")
ERROR_PATTERN = re.compile(r"(?i)\b(error|failed|exception)\b")


def parse_jenkins_log(
    log_text: str,
    pipeline_name: str,
    build_id: str
) -> List[PipelineEvent]:

    events: List[PipelineEvent] = []
    current_stage = None
    current_step_label = None
    current_step_start = None

    for line in log_text.splitlines():
        raw_line = line.strip()
        if not raw_line:
            continue

        # Detect stage
        stage_match = STAGE_PATTERN.search(raw_line)
        if stage_match:
            current_stage = stage_match.group(1)
            current_step_label = None
            current_step_start = None
            continue

        # Detect step START only
        step_match = detect_step_start(raw_line)
        if step_match:
            current_step_label = step_match.label
            current_step_start = step_match.start_line

        # Detect log level
        log_level = "ERROR" if ERROR_PATTERN.search(raw_line) else "INFO"

        event = PipelineEvent(
            pipeline_name=pipeline_name,
            build_id=build_id,
            stage_name=current_stage,
            step_name=current_step_label,
            origin_step=current_step_start,   # <-- THIS is correct
            timestamp=None,
            log_level=log_level,
            message=raw_line,
            raw_line=raw_line,
            source="jenkins"
        )

        events.append(event)

    return events
