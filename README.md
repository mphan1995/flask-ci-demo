# WebRTC Peer Simulator

**Watermark:** Max Phan - DevOps | +84 77 9050531

## Mục đích
Mô phỏng nhiều WebRTC peer với media giả lập (video/audio synthetic) để:
- Test tải cho SFU/MCU và hạ tầng signaling.
- Kiểm thử CI/CD không cần webcam/micro thật.
- Thử nghiệm UI/Browser WebRTC khi không có thiết bị.

## Hệ thống làm gì?
- Khởi tạo peer giả lập bằng Python/aiortc, tạo video/audio synthetic (OpenCV/NumPy).
- Đàm phán signaling qua HTTP/WS (Flask), kết nối đến SFU/MCU hoặc trình duyệt.
- Quản lý vòng đời peer (create → negotiate → stream → stop), thu thập metrics cơ bản.
- Điều khiển qua REST hoặc UI web (mode interactive), chạy headless cho CI.

## Không nên dùng để
- Thay thế production media pipelines thực; đây là giả lập, không bảo đảm QoE người dùng thật.
- Kiểm thử bảo mật/tấn công lưu lượng thực tế.
- Streaming media thật từ thiết bị (không hỗ trợ webcam/mic).

## Cách chạy nhanh
1. Cài đặt: `make install` (hoặc `make install-dev` để có pytest).
2. Chạy interactive UI: `make run-interactive` (có thể đổi cổng: `WRTC_SIM_PORT=8090 make run-interactive`).
3. Chạy headless scenario: `make run-headless` (hoặc `make run-scenario SCENARIO=configs/scenarios/multi-peer-load.yaml`).
4. Mở trình duyệt: `http://localhost:<port>/` → UI tại `/ui`.

## Hướng dẫn UI
- Tạo peer: nhập `Target URL` (điểm signaling/SFU), chọn video/audio profile, bấm **Create**.
- Scale peers: nhập `Target Count` và (nếu cần) URL/profile áp dụng cho peers mới, bấm **Scale**.
- Stop peer: nút **Stop** ở từng dòng; **Stop All** dừng toàn bộ.
- Refresh: tự động 4s/lần; health ping 7s/lần; có nút **Refresh** thủ công.
- Logs: hiển thị hành động/lỗi; **Clear** để xoá.

## Cấu hình chính
- `configs/app.yaml`: mode, host/port, signaling/control bật/tắt.
- `configs/scenarios/*.yaml`: định nghĩa số lượng peer, pace, churn.
- `configs/media/*.yaml`: cấu hình video/audio synthetic.
- `.env.example`: biến môi trường (STUN/TURN, scenario file, metrics).

## Tài liệu kiến trúc
- `docs/architecture.md`, `docs/file-responsibilities.md`, `docs/execution-flow.md`, `docs/signaling-flow.md`, `docs/state-model.md`, `docs/operations-wsl2.md`.

## Giới hạn & lưu ý
- Chưa tích hợp WS signaling thực tế (placeholder); cần bổ sung flask-sock/ASGI cho websocket.
- Metrics/exporters ở mức placeholder (log). Cần Prometheus/OTel nếu dùng production-like.
- UI dùng JS thuần, không build step; giữ nhẹ để chạy được ngay trên Flask dev server.

## Watermark hiển thị
- Trang UI: góc dưới hiển thị “Max Phan - DevOps | +84 77 9050531”.
- README: watermark ở đầu file (mục này).
