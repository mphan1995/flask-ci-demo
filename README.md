# MAX_ENGINE_WIN11

Local-only Flask app for safe Windows 11 optimization. Default mode is read-only (scan + plan). Apply only runs when the user clicks Apply and runs with Administrator privileges.

## English

### Features

- Dry-run by default (no changes).
- Backup + rollback for services, scheduled tasks, and registry values.
- JSON + text logs for every run.
- Skip core services (Windows Update, Defender core, networking, RPC, WMI).
- Full scan of running services (read-only) before enabling actions.
- Idempotent operations (safe to re-apply).
- Detected CPU-heavy service rules generated after scan and shown in Rule Arsenal.

### Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

Open http://127.0.0.1:5050

Pages:

- `/list` for the full service ledger
- `/check` for local verification of targeted services
- `/processes` for memory-heavy apps and related service hints

### Run elevated (Administrator)

Apply and rollback require Administrator rights. The app auto-requests elevation when started on Windows (UAC prompt). If you cancel, the app exits.

Manual option:

1. Search "Windows Terminal"
2. Right click and choose "Run as administrator"
3. Activate the venv and run `python app.py`

For CPU-heavy service detection (PID + CPU), run as Administrator. Without admin, detected CPU rules may be empty.

### Rule engine

Rules are merged from:

- `config/rules.default.json` (static rules)
- `scripts/data/rules.detected.json` (auto-generated after scan)

Each rule defines:

- `type`: registry | service | task
- `targets`: list of targets
- `detect`: state that counts as "disabled"
- `apply`: desired state
- `rollback`: restore from backup

### Data paths

- Backups: `scripts/data/backup/<backup_id>/backup.json`
- Logs: `scripts/data/logs/`
- Detected rules: `scripts/data/rules.detected.json`

### API

- `GET /api/health`
- `GET /api/scan`
- `POST /api/apply` body: `{ "selected_actions": ["rule_id"], "mode": "dry_run|apply", "action": "disable|enable" }`
- `POST /api/rollback` body: `{ "rollback_id": "<backup_id>" }`
- `GET /api/history`
- `GET /api/logs/<id>`
- `GET /api/services`
- `GET /api/processes`

### Safety notes

- No file deletions.
- Core services are not targeted.
- Always run a scan and dry-run plan before apply.
- Rollback uses the backup id from the apply summary.

### Development

This project does not use a database. All state is stored in the filesystem for local use.

### Author

- Creator: Max Phan
- Zalo: +84 77 9050531
- Facebook: https://www.facebook.com/facebookcuamax/

### Fun notes

- Designed to run locally; no external network calls in the app code.
- Every apply creates a rollback point.
- Rules are plain JSON so they are easy to audit and edit.
- Detected CPU rules refresh on each scan.
- Resource Monitor highlights memory-heavy apps and related services.

## Tiếng Việt

### Tính năng

- Mặc định dry-run (không thay đổi).
- Backup + rollback cho service, scheduled task và registry.
- Log JSON + text cho mỗi lần chạy.
- Bỏ qua core services (Windows Update, Defender core, networking, RPC, WMI).
- Quét toàn bộ service đang chạy (read-only) trước khi áp dụng.
- Idempotent (an toàn khi áp dụng lại).
- Tự tạo rule cho service ngốn CPU sau khi scan và hiển thị trong Rule Arsenal.

### Cài đặt

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Chạy

```bash
python app.py
```

Mở http://127.0.0.1:5050

Trang:

- `/list` để xem đầy đủ service ledger
- `/check` để kiểm tra local các service mục tiêu
- `/processes` để xem app ngốn RAM và gợi ý service liên quan

### Chạy với quyền Administrator

Apply và rollback cần quyền Administrator. App sẽ tự yêu cầu UAC khi khởi chạy. Nếu bạn hủy, app sẽ thoát.

Thủ công:

1. Tìm "Windows Terminal"
2. Chuột phải và chọn "Run as administrator"
3. Kích hoạt venv và chạy `python app.py`

Để phát hiện service ngốn CPU (PID + CPU), nên chạy quyền Administrator. Nếu không, detected rules có thể trống.

### Rule engine

Rules được gộp từ:

- `config/rules.default.json` (rule tĩnh)
- `scripts/data/rules.detected.json` (tự tạo sau khi scan)

Mỗi rule gồm:

- `type`: registry | service | task
- `targets`: danh sách mục tiêu
- `detect`: trạng thái được coi là "disabled"
- `apply`: trạng thái áp dụng
- `rollback`: khôi phục từ backup

### Đường dẫn dữ liệu

- Backups: `scripts/data/backup/<backup_id>/backup.json`
- Logs: `scripts/data/logs/`
- Detected rules: `scripts/data/rules.detected.json`

### API

- `GET /api/health`
- `GET /api/scan`
- `POST /api/apply` body: `{ "selected_actions": ["rule_id"], "mode": "dry_run|apply", "action": "disable|enable" }`
- `POST /api/rollback` body: `{ "rollback_id": "<backup_id>" }`
- `GET /api/history`
- `GET /api/logs/<id>`
- `GET /api/services`
- `GET /api/processes`

### Lưu ý an toàn

- Không xóa file.
- Không đụng core services.
- Luôn scan + dry-run trước khi apply.
- Rollback dùng backup id trong apply summary.

### Phát triển

Project không dùng database. Mọi state được lưu trong filesystem.

### Tác giả

- Người tạo: Max Phan
- Zalo: +84 77 9050531
- Facebook: https://www.facebook.com/facebookcuamax/

### Thông tin vui

- Thiết kế chạy local; không gọi mạng ngoài trong app code.
- Mỗi lần Apply đều tạo điểm rollback.
- Rules là JSON nên dễ đọc và dễ chỉnh.
- Detected CPU rules được làm mới theo mỗi lần scan.
- Resource Monitor giúp nhìn nhanh app ngốn RAM và map service liên quan.
