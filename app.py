from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request

from analyzers.log_parser import parse_jenkins_log
from analyzers.rule_engine import analyze_events
from analyzers.ai_reasoner import AIExplainRequest, explain_with_ai
from analyzers.context_builder import build_evidence_window, summarize_timeline

APP_DISPLAY_NAME = "DevOps AI By MaX Phan"
BASE_DIR = Path(__file__).resolve().parent
SAMPLE_LOG_PATH = BASE_DIR / "data" / "sample_logs" / "jenkins_fail.log"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export "):].strip()
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(BASE_DIR / ".env")


def analyze_log_text(
    log_text: str,
    pipeline_name: str,
    build_id: str,
    provider: str = "mock"
) -> Dict[str, Any]:
    events = parse_jenkins_log(
        log_text=log_text,
        pipeline_name=pipeline_name,
        build_id=build_id
    )

    result = analyze_events(events)

    # pick a best-guess stage from last ERROR event
    last_error_stage = None
    for e in reversed(events):
        if e.log_level == "ERROR" and e.stage_name:
            last_error_stage = e.stage_name
            break

    context_events = build_evidence_window(events)
    timeline = summarize_timeline(context_events)

    req = AIExplainRequest(
        pipeline_name=pipeline_name,
        build_id=build_id,
        stage_name=last_error_stage,
        origin_step=result.origin_step,
        failure_surface=result.failure_surface,
        root_cause=result.root_cause,
        confidence=result.confidence,
        evidence=result.evidence,
        timeline=timeline
    )

    md = explain_with_ai(req, provider=provider)

    return {
        "pipeline_name": pipeline_name,
        "build_id": build_id,
        "stage_name": last_error_stage,
        "root_cause": result.root_cause,
        "confidence": result.confidence,
        "evidence": result.evidence,
        "origin_step": result.origin_step,
        "failure_surface": result.failure_surface,
        "timeline": timeline,
        "report_markdown": md,
        "event_count": len(events)
    }


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index() -> str:
        return render_template(
            "index.html",
            app_name=APP_DISPLAY_NAME,
            default_pipeline_name="flask-ci-demo",
            default_build_id="42"
        )

    @app.route("/api/sample-log")
    def sample_log() -> str:
        if not SAMPLE_LOG_PATH.exists():
            return "", 404
        return SAMPLE_LOG_PATH.read_text(encoding="utf-8")

    @app.route("/api/analyze", methods=["POST"])
    def analyze() -> Any:
        payload = request.get_json(silent=True) or {}
        log_text = (payload.get("log_text") or "").strip()
        pipeline_name = (payload.get("pipeline_name") or "flask-ci-demo").strip()
        build_id = (payload.get("build_id") or "42").strip()
        provider = (payload.get("provider") or "mock").strip()

        if not log_text:
            return jsonify({"error": "Log text is required."}), 400

        if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
            return jsonify({"error": "OPENAI_API_KEY is not set."}), 400

        try:
            result = analyze_log_text(
                log_text=log_text,
                pipeline_name=pipeline_name,
                build_id=build_id,
                provider=provider
            )
        except Exception as exc:  # pragma: no cover - fallback safety
            return jsonify({"error": f"Analysis failed: {exc}"}), 500

        return jsonify(result)

    return app


def run_cli_sample() -> None:
    log_text = SAMPLE_LOG_PATH.read_text(encoding="utf-8")
    result = analyze_log_text(
        log_text=log_text,
        pipeline_name="flask-ci-demo",
        build_id="42",
        provider="mock"
    )
    print(result["report_markdown"])

    reports_dir = BASE_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "output.md").write_text(result["report_markdown"], encoding="utf-8")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli_sample()
    else:
        app = create_app()
        port = int(os.environ.get("PORT", "5000"))
        app.run(host="0.0.0.0", port=port, debug=True)
