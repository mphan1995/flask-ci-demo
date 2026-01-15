# Windows Optimize Services Engine - Platform

A local-only Flask app to safely review and apply Windows 11 service tweaks. It starts in read-only scan mode, and only makes changes when you click Apply and run as Administrator.

## Features

- Starts with a dry-run plan (no changes)
- Backup + rollback for services, scheduled tasks, and registry values
- JSON + text logs for every run
- Core services are excluded (Windows Update, Defender core, networking, RPC, WMI)
- Full scan before any actions
- Idempotent operations (safe to re-apply)

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:5050

Extra pages:

- `/list` for the full service ledger
- `/check` for local verification of targeted services
- `/processes` for memory-heavy apps and related service hints

## Run elevated (Administrator)

Apply and rollback require Administrator rights. On Windows, the app prompts for elevation (UAC). If you cancel, the app exits.

Manual option:

1. Search "Windows Terminal"
2. Right click and choose "Run as administrator"
3. Activate the venv and run `python app.py`

The UI shows an Admin status badge.

## API

- `GET /api/health`
- `GET /api/scan`
- `POST /api/apply` body: `{ "selected_actions": ["rule_id"], "mode": "dry_run|apply", "action": "disable|enable" }`
- `POST /api/rollback` body: `{ "rollback_id": "<backup_id>" }`
- `GET /api/history`
- `GET /api/logs/<id>`
- `GET /api/services`
- `GET /api/processes`

## Data paths

- Backups: `scripts/data/backup/<backup_id>/backup.json`
- Logs: `scripts/data/logs/`

## Rule engine

Rules live in `config/rules.default.json` and are grouped by category. Each rule defines:

- `type`: registry | service | task
- `targets`: list of targets
- `detect`: state that counts as "disabled"
- `apply`: desired state
- `rollback`: restore from backup

Add a new rule by appending an entry that follows the same schema and reload the app.

## Safety notes

- No file deletions.
- Core services are not targeted.
- Always run a scan and dry-run plan before apply.
- Rollback uses the backup id from the apply summary.

## Development

This project does not use a database. All state is stored in the filesystem for local use.

---

# Windows Optimize Services Engine - Platform (Tiếng Việt)

Ứng dụng Flask chạy cục bộ giúp bạn xem xét và áp dụng các tinh chỉnh dịch vụ Windows 11 một cách an toàn. Ứng dụng luôn bắt đầu ở chế độ quét chỉ đọc, và chỉ thay đổi khi bạn bấm Apply và chạy quyền Administrator.

## Tính năng

- Luôn chạy thử (dry-run) trước, không chỉnh sửa hệ thống
- Sao lưu và hoàn tác cho service, scheduled task, và registry
- Có log JSON + text cho mỗi lần chạy
- Bỏ qua các dịch vụ cốt lõi (Windows Update, Defender core, networking, RPC, WMI)
- Quét đầy đủ trước khi áp dụng
- Thao tác lặp lại an toàn

## Cài đặt

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Chạy

```bash
python app.py
```

Mở http://127.0.0.1:5050

Trang bổ sung:

- `/list` xem toàn bộ danh sách service
- `/check` kiểm tra nhanh các dịch vụ mục tiêu
- `/processes` gợi ý app ngốn RAM và dịch vụ liên quan

## Chạy quyền Administrator

Apply và rollback cần quyền Administrator. Trên Windows, ứng dụng sẽ tự hỏi UAC. Nếu bạn hủy, ứng dụng sẽ thoát.

Cách thủ công:

1. Tìm "Windows Terminal"
2. Chuột phải chọn "Run as administrator"
3. Kích hoạt venv và chạy `python app.py`

Giao diện sẽ hiển thị trạng thái Admin.

## API

- `GET /api/health`
- `GET /api/scan`
- `POST /api/apply` body: `{ "selected_actions": ["rule_id"], "mode": "dry_run|apply", "action": "disable|enable" }`
- `POST /api/rollback` body: `{ "rollback_id": "<backup_id>" }`
- `GET /api/history`
- `GET /api/logs/<id>`
- `GET /api/services`
- `GET /api/processes`

## Đường dẫn dữ liệu

- Backup: `scripts/data/backup/<backup_id>/backup.json`
- Logs: `scripts/data/logs/`

## Rule engine

Rules nằm trong `config/rules.default.json` và được nhóm theo danh mục. Mỗi rule gồm:

- `type`: registry | service | task
- `targets`: danh sách mục tiêu
- `detect`: trạng thái được coi là "disabled"
- `apply`: trạng thái cần đặt
- `rollback`: khôi phục từ bản sao lưu

Thêm rule mới bằng cách thêm entry theo đúng schema rồi reload app.

## Lưu ý an toàn

- Không xóa file.
- Không đụng đến dịch vụ cốt lõi.
- Luôn quét và chạy dry-run trước khi áp dụng.
- Rollback dùng backup id từ phần tóm tắt sau khi apply.

## Development

Dự án không dùng database. Toàn bộ trạng thái lưu trong filesystem để dùng cục bộ.
