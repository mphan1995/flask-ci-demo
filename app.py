from analyzers.log_parser import parse_jenkins_log
from analyzers.rule_engine import analyze_events

with open("data/sample_logs/jenkins_fail.log") as f:
    log_text = f.read()

events = parse_jenkins_log(
    log_text,
    pipeline_name="flask-ci-demo",
    build_id="42"
)

result = analyze_events(events)
print(result)
