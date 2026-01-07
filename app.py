from analyzers.log_parser import parse_jenkins_log
from analyzers.rule_engine import analyze_events
from analyzers.ai_reasoner import AIExplainRequest, explain_with_ai

def main():
    with open("data/sample_logs/jenkins_fail.log", "r", encoding="utf-8") as f:
        log_text = f.read()

    events = parse_jenkins_log(
        log_text=log_text,
        pipeline_name="flask-ci-demo",
        build_id="42"
    )

    result = analyze_events(events)

    # pick a best-guess stage from last ERROR event
    last_error_stage = None
    for e in reversed(events):
        if e.log_level == "ERROR" and e.stage_name:
            last_error_stage = e.stage_name
            break

    req = AIExplainRequest(
        pipeline_name="flask-ci-demo",
        build_id="42",
        stage_name=last_error_stage,
        root_cause=result.root_cause,
        confidence=result.confidence,
        evidence=result.evidence
    )

    md = explain_with_ai(req, provider="mock")
    print(md)

    # optionally write report
    with open("reports/output.md", "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    main()
