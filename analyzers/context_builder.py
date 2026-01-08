from typing import List, Optional
from models.pipeline_event import PipelineEvent


def build_evidence_window(
    events: List[PipelineEvent],
    window_before: int = 30,
    window_after: int = 10
) -> List[PipelineEvent]:
    """
    Build a context window around the last ERROR event,
    scoped to the same stage.
    """

    last_error_index: Optional[int] = None

    for i in range(len(events) - 1, -1, -1):
        if events[i].log_level == "ERROR":
            last_error_index = i
            break

    if last_error_index is None:
        return []

    error_event = events[last_error_index]
    stage = error_event.stage_name

    scoped_events = [
        e for e in events
        if e.stage_name == stage
    ]

    # find index within scoped events
    scoped_index = scoped_events.index(error_event)

    start = max(0, scoped_index - window_before)
    end = min(len(scoped_events), scoped_index + window_after + 1)

    return scoped_events[start:end]

def summarize_timeline(events: List[PipelineEvent]) -> List[str]:
    """
    Convert events into human-readable timeline lines.
    """
    timeline = []
    for e in events:
        step = f" | {e.step_name}" if e.step_name else ""
        prefix = f"[{e.stage_name or 'UNKNOWN'}{step}]"
        timeline.append(f"{prefix} {e.log_level}: {e.message}")
    return timeline
