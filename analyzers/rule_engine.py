from typing import Iterable, List, Optional, Set
from models.pipeline_event import PipelineEvent
from models.analysis_result import AnalysisResult
from analyzers.knowledge_base import (
    CAUSAL_MAPPING,
    CAUSAL_PREFIX_MAP,
    DOMAIN_FALLBACKS,
    ERROR_SIGNATURES,
    STEP_DOMAIN_MAP
)


def _first_error_match(
    error_events: Iterable[PipelineEvent],
    keywords: List[str],
    allowed_steps: Optional[Set[str]] = None
) -> Optional[PipelineEvent]:
    for event in error_events:
        message = event.message.lower()
        if not any(keyword in message for keyword in keywords):
            continue
        if allowed_steps and event.step_name not in allowed_steps:
            continue
        return event
    return None


def _event_origin(event: Optional[PipelineEvent]) -> Optional[str]:
    if not event:
        return None
    return event.origin_step or event.step_name or event.stage_name


def _event_surface(event: Optional[PipelineEvent]) -> Optional[str]:
    if not event:
        return None
    return event.step_name or event.stage_name


def _allowed_steps_for(root_cause: str, explicit_steps: Optional[Set[str]]) -> Optional[Set[str]]:
    if explicit_steps:
        return explicit_steps

    mapping = CAUSAL_MAPPING.get(root_cause)
    if mapping and mapping.get("origin_steps"):
        return mapping["origin_steps"]

    for prefix, mapping_key in CAUSAL_PREFIX_MAP:
        if root_cause.startswith(prefix):
            return CAUSAL_MAPPING.get(mapping_key, {}).get("origin_steps")

    return None


def _event_domain(event: Optional[PipelineEvent]) -> Optional[str]:
    if not event or not event.step_name:
        return None
    return STEP_DOMAIN_MAP.get(event.step_name)


def _first_error_with_domain(
    error_events: Iterable[PipelineEvent],
    domain: str
) -> Optional[PipelineEvent]:
    for event in error_events:
        if _event_domain(event) == domain:
            return event
    return None


def analyze_events(events: List[PipelineEvent]) -> AnalysisResult:
    """
    Analyze pipeline events using deterministic rules
    before handing off to AI reasoning.
    """

    error_events = [e for e in events if e.log_level == "ERROR"]

    evidence = [e.raw_line for e in error_events[-5:]]  # last errors
    last_error_event = error_events[-1] if error_events else None
    failure_surface = _event_surface(last_error_event)

    for signature in ERROR_SIGNATURES:
        allowed_steps = _allowed_steps_for(signature.root_cause, signature.allowed_steps)
        origin_event = _first_error_match(
            error_events,
            signature.keywords,
            allowed_steps=allowed_steps
        )
        if origin_event:
            return AnalysisResult(
                root_cause=signature.root_cause,
                confidence=signature.confidence,
                evidence=evidence,
                origin_step=_event_origin(origin_event),
                failure_surface=failure_surface
            )

    for domain, (root_cause, confidence) in DOMAIN_FALLBACKS.items():
        origin_event = _first_error_with_domain(error_events, domain)
        if origin_event:
            return AnalysisResult(
                root_cause=root_cause,
                confidence=confidence,
                evidence=evidence,
                origin_step=_event_origin(origin_event),
                failure_surface=failure_surface
            )

    # --- Rule 5: Build config ---
    if any("build" in e.stage_name.lower() for e in error_events if e.stage_name):
        return AnalysisResult(
            root_cause="BUILD_CONFIG_ERROR",
            confidence=0.5,
            evidence=evidence,
            origin_step=None,
            failure_surface=failure_surface
        )

    return AnalysisResult(
        root_cause="UNKNOWN",
        confidence=0.3,
        evidence=evidence,
        origin_step=None,
        failure_surface=failure_surface
    )
