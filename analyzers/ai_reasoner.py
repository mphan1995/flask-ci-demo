from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import List, Optional
import urllib.error
import urllib.request

from analyzers.knowledge_base import DOMAIN_HINTS, infer_domain

@dataclass
class AIExplainRequest:
    pipeline_name: str
    build_id: str
    stage_name: Optional[str]
    origin_step: Optional[str]
    failure_surface: Optional[str]
    root_cause: str
    confidence: float
    evidence: List[str]
    timeline: Optional[List[str]] = None



def _load_prompt_template(path: str = "prompts/root_cause_prompt.txt") -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(req: AIExplainRequest) -> str:
    template = _load_prompt_template()

    stage = req.stage_name or "UNKNOWN"
    origin_step = req.origin_step or "UNKNOWN"
    failure_surface = req.failure_surface or stage

    evidence_block = "\n".join(
        [f"- `{line}`" for line in req.evidence[:15]]
    ) or "- (no explicit error lines captured)"

    timeline_block = ""
    if req.timeline:
        timeline_block = "\nTimeline (context window):\n" + "\n".join(
            [f"- {line}" for line in req.timeline[:40]]
        )

    domain = infer_domain(req.root_cause, req.origin_step, req.failure_surface)
    domain_hints = DOMAIN_HINTS.get(domain or "", [])
    domain_block = ""
    if domain_hints:
        domain_block = "\nDomain hints:\n" + "\n".join(
            [f"- {hint}" for hint in domain_hints]
        )

    context = f"""
Pipeline: {req.pipeline_name}
Build ID: {req.build_id}
Stage: {stage}
Root cause origin: {origin_step}
Failure surface: {failure_surface}

Rule-based root cause: {req.root_cause}
Rule confidence: {req.confidence}

Key evidence:
{evidence_block}
{timeline_block}
{domain_block}
""".strip()

    return f"{template}\n\n---\n\n{context}\n"


def _read_env_float(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _call_openai_chat(prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    temperature = _read_env_float("OPENAI_TEMPERATURE", 0.2)
    timeout_s = _read_env_float("OPENAI_TIMEOUT", 30.0)

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            response = json.load(resp)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise ValueError(f"OpenAI API error: {body}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"OpenAI request failed: {exc.reason}") from exc

    choices = response.get("choices") or []
    if not choices:
        raise ValueError("OpenAI response missing choices.")

    message = (choices[0].get("message") or {}).get("content")
    if not message:
        raise ValueError("OpenAI response missing content.")

    return message.strip()


def explain_with_ai(
    req: AIExplainRequest,
    provider: str = "mock",
) -> str:
    """
    Explain & suggest fixes based on rule output.
    EXPLAIN_ONLY: AI must not override root cause.
    provider:
      - 'mock': returns deterministic Markdown (no API needed)
      - 'openai': calls OpenAI using env config
    """
    prompt = build_prompt(req)

    if provider == "mock":
        # Deterministic mock to keep dev moving
        evidence_md = "\n".join([f"- `{x}`" for x in req.evidence[:10]]) or "- (none)"
        origin_step = req.origin_step or "UNKNOWN"
        failure_surface = req.failure_surface or (req.stage_name or "UNKNOWN")
        return f"""## Executive summary
Pipeline **{req.pipeline_name}** (build **{req.build_id}**) failed at stage **{req.stage_name or "UNKNOWN"}**.
Rule-based classification indicates **{req.root_cause}** (confidence {req.confidence}).

## Rule-based root cause
**{req.root_cause}**

## Root cause origin
**{origin_step}**

## Failure surface
**{failure_surface}**

## AI hypothesis (non-authoritative)
Based on the current evidence, the most likely failure mode aligns with **{req.root_cause}**,
but validate with the diagnostics below before making structural changes.

## Key evidence
{evidence_md}

## Remediation options
1. Re-check dependency declarations (requirements / versions) and pin known-good versions.
2. Clear caches / rebuild environment and retry with a clean workspace.
3. Verify package index / registry access and authentication (if applicable).
4. Add retries/backoff for transient failures and ensure deterministic builds.

## Diagnostic checks
- Re-run the failing command locally with verbose flags.
- Print versions (`python --version`, `pip --version`, `java -version`, etc.) in the pipeline.
- Check network/DNS/proxy settings in the agent.
- Capture artifact logs and environment snapshot for comparison.

## Missing or uncertain information
- Exact failing command output and its exit code.
- The dependency file (requirements.txt / pom.xml / build.gradle) and resolver config.
- Agent environment details (OS, runtime versions, proxy).
"""
    elif provider == "openai":
        return _call_openai_chat(prompt)
    else:
        raise ValueError(f"Unknown provider: {provider}")
