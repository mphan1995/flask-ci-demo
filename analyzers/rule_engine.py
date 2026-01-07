from typing import List
from models.pipeline_event import PipelineEvent
from models.analysis_result import AnalysisResult


def analyze_events(events: List[PipelineEvent]) -> AnalysisResult:
    """
    Analyze pipeline events using deterministic rules
    before handing off to AI reasoning.
    """

    error_events = [e for e in events if e.log_level == "ERROR"]
    info_events = [e for e in events if e.log_level == "INFO"]

    evidence = [e.raw_line for e in error_events[-5:]]  # last errors

    # --- Rule 1: Dependency issues ---
    for e in error_events:
        if any(k in e.message.lower() for k in [
            "could not find a version",
            "dependency",
            "requirements.txt",
            "no matching distribution"
        ]):
            return AnalysisResult(
                root_cause="DEPENDENCY_ERROR",
                confidence=0.75,
                evidence=evidence
            )

    # --- Rule 2: Permission / IAM ---
    for e in error_events:
        if any(k in e.message.lower() for k in [
            "permission denied",
            "access denied",
            "unauthorized"
        ]):
            return AnalysisResult(
                root_cause="PERMISSION_ERROR",
                confidence=0.8,
                evidence=evidence
            )

    # --- Rule 3: Network ---
    for e in error_events:
        if any(k in e.message.lower() for k in [
            "timeout",
            "connection refused",
            "network is unreachable"
        ]):
            return AnalysisResult(
                root_cause="NETWORK_ERROR",
                confidence=0.7,
                evidence=evidence
            )

    # --- Rule 4: Script / command ---
    for e in error_events:
        if "command not found" in e.message.lower():
            return AnalysisResult(
                root_cause="SCRIPT_ERROR",
                confidence=0.6,
                evidence=evidence
            )

    # --- Rule 5: Build config ---
    if any("build" in e.stage_name.lower() for e in error_events if e.stage_name):
        return AnalysisResult(
            root_cause="BUILD_CONFIG_ERROR",
            confidence=0.5,
            evidence=evidence
        )

    return AnalysisResult(
        root_cause="UNKNOWN",
        confidence=0.3,
        evidence=evidence
    )
