from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import os

from models.pipeline_event import PipelineEvent
from models.analysis_result import AnalysisResult


@dataclass
class AIExplainRequest:
    pipeline_name: str
    build_id: str
    stage_name: Optional[str]
    root_cause: str
    confidence: float
    evidence: List[str]


def _load_prompt_template(path: str = "prompts/root_cause_prompt.txt") -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(req: AIExplainRequest) -> str:
    template = _load_prompt_template()

    evidence_block = "\n".join([f"- `{line}`" for line in req.evidence[:15]])  # limit
    stage = req.stage_name or "UNKNOWN"

    context = f"""
Pipeline: {req.pipeline_name}
Build ID: {req.build_id}
Stage: {stage}
Rule-based root cause: {req.root_cause}
Rule confidence: {req.confidence}
Evidence:
{evidence_block}
""".strip()

    return f"{template}\n\n---\n\n{context}\n"


def explain_with_ai(
    req: AIExplainRequest,
    provider: str = "mock",
) -> str:
    """
    Explain & suggest fixes based on rule output.
    EXPLAIN_ONLY: AI must not override root cause.
    provider:
      - 'mock': returns deterministic Markdown (no API needed)
      - 'openai': calls OpenAI (you can wire later)
    """
    prompt = build_prompt(req)

    if provider == "mock":
        # Deterministic mock to keep dev moving
        evidence_md = "\n".join([f"- `{x}`" for x in req.evidence[:10]]) or "- (none)"
        return f"""## Summary
Pipeline **{req.pipeline_name}** (build **{req.build_id}**) failed at stage **{req.stage_name or "UNKNOWN"}**.
Rule-based classification indicates **{req.root_cause}** (confidence {req.confidence}).

## Root cause (rule-based)
**{req.root_cause}**

## Evidence
{evidence_md}

## Fix suggestions
1. Re-check dependency declarations (requirements / versions) and pin known-good versions.
2. Clear caches / rebuild environment and retry with a clean workspace.
3. Verify package index / registry access and authentication (if applicable).
4. Add retries/backoff for transient failures and ensure deterministic builds.

## Diagnostic checks
- Re-run the failing command locally with verbose flags.
- Print versions (`python --version`, `pip --version`, `java -version`, etc.) in the pipeline.
- Check network/DNS/proxy settings in the agent.
- Capture artifact logs and environment snapshot for comparison.

## Missing info
- Exact failing command output and its exit code.
- The dependency file (requirements.txt / pom.xml / build.gradle) and resolver config.
- Agent environment details (OS, runtime versions, proxy).
"""
    elif provider == "openai":
        # Placeholder: keep codebase clean; wire later when you want.
        # We intentionally don't implement API calls here to avoid coupling.
        raise NotImplementedError(
            "OpenAI provider not wired yet. Use provider='mock' for now."
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")
