from analyzers.log_parser import parse_jenkins_log

with open("data/sample_logs/jenkins_fail.log") as f:
    log_text = f.read()

events = parse_jenkins_log(
    log_text=log_text,
    pipeline_name="flask-ci-demo",
    build_id="42"
)

for e in events:
    if e.log_level == "ERROR":
        print(e)
