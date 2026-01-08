# AI-DEVOPS-ASSIST

> Watermark: Max Phan from Endava VN

AI-DEVOPS-ASSIST là dự án phân tích lỗi pipeline CI/CD theo hướng *Rules-first, AI-assisted*.
Mục tiêu là giúp DevOps/SRE nhìn nhanh **nguyên nhân gốc**, **nguồn gốc phát sinh**, và **bề mặt lỗi** dựa trên log thực tế.

## Tính năng chính
- Phân tích log Jenkins, chuẩn hóa thành sự kiện pipeline có stage/step.
- Phân loại root cause bằng rule engine (deterministic, dễ kiểm chứng).
- Tách rõ:
  - **Root cause origin**: ERROR đầu tiên phù hợp với category trong step hợp lệ.
  - **Failure surface**: ERROR cuối cùng nơi pipeline fail bộc lộ.
- Detect step quan trọng: `pip install`, `docker build`, `helm upgrade`, `kubectl apply`,
  `kubectl rollout`, `terraform plan/apply`, `ansible-playbook`, `git clone/fetch/pull/push`.
- UI trực quan: nhập log, xem evidence, timeline, báo cáo AI.
- Tích hợp OpenAI (tuỳ chọn) để tạo consultant narrative.
- Rule pack mở rộng cho: Kubernetes, Terraform, Ansible, Prometheus, Loki, Grafana, Git.

## Kiến trúc tổng quan
```
logs -> log_parser -> events -> rule_engine -> analysis_result
                           \-> context_builder -> timeline
analysis_result + context -> ai_reasoner -> report (Markdown)
```

## Chạy nhanh (UI)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Nhập OPENAI_API_KEY trong .env nếu muốn dùng OpenAI

python app.py
```
Mở `http://localhost:5000` để dùng UI.

## Chạy nhanh (CLI)
```bash
python app.py --cli
```
Kết quả sẽ được ghi vào `reports/output.md`.

## Biến môi trường (.env)
- `OPENAI_API_KEY`: API key của OpenAI (bắt buộc nếu chọn provider OpenAI).
- `OPENAI_MODEL`: mặc định `gpt-4o-mini`.
- `OPENAI_API_BASE`: mặc định `https://api.openai.com/v1`.
- `OPENAI_TEMPERATURE`: mặc định `0.2`.
- `OPENAI_TIMEOUT`: mặc định `30` giây.

## Mở rộng rule / step
- Thêm pattern step trong `analyzers/step_detector.py`.
- Thêm rule phân loại trong `analyzers/rule_engine.py`.
- Prompt cho AI nằm trong `prompts/root_cause_prompt.txt`.

## Sample logs
Các log mẫu nằm trong `data/sample_logs/` để demo nhanh:
- `jenkins_fail.log`
- `kubernetes_fail.log`
- `terraform_fail.log`
- `ansible_fail.log`
- `prometheus_fail.log`
- `loki_fail.log`
- `grafana_fail.log`
- `git_fail.log`

## Gợi ý nâng cấp tiếp theo
- Parse timestamp/step chi tiết từ Jenkins log.
- Thêm rule pack theo từng hệ sinh thái (Python, Java, Node, Kubernetes).
- Correlate error theo stage + step + artifact để tăng độ chính xác.
- Hỗ trợ nhiều nguồn log: GitLab CI, GitHub Actions.

---
Nếu bạn cần thêm rule hoặc step mapping mới, hãy tạo issue hoặc gửi yêu cầu cụ thể qua max.phan@endava.com .
Xin cám ơn !!!
