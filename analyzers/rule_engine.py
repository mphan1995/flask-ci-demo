from typing import Iterable, List, Optional, Set
from models.pipeline_event import PipelineEvent
from models.analysis_result import AnalysisResult


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


def _first_error_in_steps(
    error_events: Iterable[PipelineEvent],
    allowed_steps: Set[str]
) -> Optional[PipelineEvent]:
    for event in error_events:
        if event.step_name in allowed_steps:
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


def analyze_events(events: List[PipelineEvent]) -> AnalysisResult:
    """
    Analyze pipeline events using deterministic rules
    before handing off to AI reasoning.
    """

    error_events = [e for e in events if e.log_level == "ERROR"]

    evidence = [e.raw_line for e in error_events[-5:]]  # last errors
    last_error_event = error_events[-1] if error_events else None
    failure_surface = _event_surface(last_error_event)

    # --- Rule 1: Dependency issues ---
    dependency_keywords = [
        "could not find a version",
        "dependency",
        "requirements.txt",
        "no matching distribution"
    ]
    origin_event = _first_error_match(
        error_events,
        dependency_keywords,
        allowed_steps={"pip install"}
    )
    if origin_event:
        return AnalysisResult(
            root_cause="DEPENDENCY_ERROR",
            confidence=0.75,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 1b: Kubernetes deployment failures ---
    kubernetes_keywords = [
        "crashloopbackoff",
        "imagepullbackoff",
        "errimagepull",
        "failedmount",
        "mountvolume.setup failed",
        "failed to pull image",
        "back-off pulling image",
        "readiness probe failed",
        "liveness probe failed",
        "exceeded its progress deadline",
        "timed out waiting for the condition",
        "failed scheduling",
        "failed to create pod",
        "pod has unbound immediate persistentvolumeclaims"
    ]
    origin_event = _first_error_match(
        error_events,
        kubernetes_keywords,
        allowed_steps={"kubectl apply", "kubectl rollout", "helm upgrade"}
    )
    if not origin_event:
        origin_event = _first_error_match(error_events, kubernetes_keywords)
    if origin_event:
        return AnalysisResult(
            root_cause="KUBERNETES_DEPLOYMENT_ERROR",
            confidence=0.7,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 1c: Terraform failures ---
    origin_event = _first_error_in_steps(
        error_events,
        {"terraform init", "terraform plan", "terraform apply"}
    )
    if not origin_event:
        origin_event = _first_error_match(
            error_events,
            [
                "terraform",
                "provider produced inconsistent result",
                "terraform apply failed",
                "terraform plan failed",
                "terraform init failed"
            ]
        )
    if origin_event:
        return AnalysisResult(
            root_cause="TERRAFORM_ERROR",
            confidence=0.7,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 1d: Ansible failures ---
    origin_event = _first_error_in_steps(
        error_events,
        {"ansible-playbook"}
    )
    if not origin_event:
        origin_event = _first_error_match(
            error_events,
            [
                "ansible",
                "unreachable!",
                "failed!",
                "fatal:"
            ]
        )
    if origin_event:
        return AnalysisResult(
            root_cause="ANSIBLE_ERROR",
            confidence=0.7,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 1e: Git failures ---
    origin_event = _first_error_in_steps(
        error_events,
        {"git clone", "git fetch", "git pull", "git push"}
    )
    if not origin_event:
        origin_event = _first_error_match(
            error_events,
            [
                "authentication failed",
                "repository not found",
                "could not read from remote repository",
                "permission denied (publickey)",
                "fatal: repository"
            ]
        )
    if origin_event:
        return AnalysisResult(
            root_cause="GIT_ERROR",
            confidence=0.65,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 1f: Prometheus failures ---
    prometheus_keywords = [
        "error scraping",
        "scrape failed",
        "scrape error",
        "remote write",
        "prometheus"
    ]
    origin_event = _first_error_match(error_events, prometheus_keywords)
    if origin_event:
        return AnalysisResult(
            root_cause="PROMETHEUS_SCRAPE_ERROR",
            confidence=0.6,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 1g: Loki failures ---
    loki_keywords = [
        "loki",
        "ingester",
        "error sending batch",
        "failed to send batch",
        "failed to flush",
        "push request failed"
    ]
    origin_event = _first_error_match(error_events, loki_keywords)
    if origin_event:
        return AnalysisResult(
            root_cause="LOKI_INGEST_ERROR",
            confidence=0.6,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 1h: Grafana failures ---
    grafana_keywords = [
        "grafana",
        "datasource",
        "dashboard",
        "alerting",
        "failed to provision"
    ]
    origin_event = _first_error_match(error_events, grafana_keywords)
    if origin_event:
        return AnalysisResult(
            root_cause="GRAFANA_ERROR",
            confidence=0.6,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 2: Permission / IAM ---
    permission_keywords = [
        "permission denied",
        "access denied",
        "unauthorized"
    ]
    origin_event = _first_error_match(error_events, permission_keywords)
    if origin_event:
        return AnalysisResult(
            root_cause="PERMISSION_ERROR",
            confidence=0.8,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 3: Network ---
    network_keywords = [
        "timeout",
        "connection refused",
        "network is unreachable"
    ]
    origin_event = _first_error_match(error_events, network_keywords)
    if origin_event:
        return AnalysisResult(
            root_cause="NETWORK_ERROR",
            confidence=0.7,
            evidence=evidence,
            origin_step=_event_origin(origin_event),
            failure_surface=failure_surface
        )

    # --- Rule 4: Script / command ---
    origin_event = _first_error_match(error_events, ["command not found"])
    if origin_event:
        return AnalysisResult(
            root_cause="SCRIPT_ERROR",
            confidence=0.6,
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
