# CloudPhone Free Telegram Bot (Production Ready)

Một Telegram Bot Python bất đồng bộ chuyên nghiệp dùng để tự động hóa quy trình đăng ký tài khoản và nhận máy dùng thử (trial 6h) trên nền tảng UmoCloud/WillClouds.

---

## 🌟 TÍNH NĂNG CHÍNH

- **Kiến trúc Layered sạch sẽ:** Phân tách rõ ràng giữa Handlers, Services, Repositories, Middlewares và Utils.
- **Bất đồng bộ 100% (Async/Await):** Sử dụng `python-telegram-bot` v21+ và `httpx.AsyncClient` non-blocking, không làm đơ bot khi có nhiều người dùng.
- **Cơ sở dữ liệu SQLite Async (aiosqlite):** Lưu trữ người dùng, lịch sử tạo tài khoản và session có độ tin cậy cao, hỗ trợ WAL mode chống race-condition.
- **Bảo mật tuyệt đối:**
  - Không hard-code Token, Secret, API Key trong mã nguồn.
  - Quản lý cấu hình bằng `pydantic-settings` với xác thực định dạng token và biến bắt buộc.
  - Mã hóa mật khẩu bằng RSA PKCS#1 v1.5.
  - Chống spam với `RateLimiter` middleware.
  - Escape HTML tự động chống lỗi vỡ định dạng và injection tin nhắn Telegram.
- **Tác vụ Admin:**
  - `/thongke`: Xem tổng số tài khoản và chi tiết theo từng user.
- **Bắt buộc tham gia nhóm (Force Join Group/Channel):**
  - Tự động kiểm tra người dùng đã tham gia nhóm Telegram chỉ định (`-1003804934789`) trước khi cho phép tạo tài khoản hoặc nhận máy dùng thử.
  - Hiển thị nút tham gia nhóm và xác minh tư cách thành viên theo thời gian thực.
- **Giới hạn số lượt tạo & Cơ chế Referral (Giới thiệu nhận lượt):**
  - Mỗi tài khoản Telegram mặc định được tạo tối đa **10 tài khoản UmoCloud 6h**.
  - Tích hợp tính năng giới thiệu bạn bè qua liên kết `t.me/<bot_username>?start=<user_id>`.
  - Nút **"🎁 Giới thiệu bạn bè"** hiển thị chi tiết link ref, số người đã giới thiệu, lượt thưởng và lượt tạo còn lại.
  - Khi người được giới thiệu tạo thành công 1 tài khoản mới, người giới thiệu sẽ tự động nhận thêm **+5 lượt tạo** và có tin nhắn thông báo realtime từ bot.


- **Web Dashboard Quản Trị Hiện Đại (TypeScript + React 19 + Tailwind CSS + FastAPI REST API):**
  - Giao diện Dark Cyberpunk / Modern Glassmorphism đẳng cấp, responsive 100% trên PC & Mobile.
  - Thống kê realtime: Tổng tài khoản đã tạo, danh sách người dùng Telegram, trạng thái hệ thống, tổng lượt thưởng.
  - **Quản lý người dùng nâng cao:** Tìm kiếm theo ID/username, sắp xếp theo lượt thưởng, tuỳ chỉnh cấp thêm/bớt lượt thưởng (Bonus turns) cho từng người dùng, xoá user, và **gửi tin nhắn riêng (Direct Message)** trực tiếp từ Admin tới Telegram user.
  - **Quản lý tài khoản toàn diện:** Tìm kiếm, xem chi tiết tình trạng nhận gói 6h, xoá tài khoản, **tạo tài khoản thủ công trực tiếp từ Web Dashboard**, và **xuất danh sách ra file CSV**.
  - **Trung tâm phát sóng thông báo (Broadcast Console):** Gửi thông báo đến toàn bộ người dùng hoặc một User ID cụ thể với các mẫu template soạn sẵn (Quà tặng, Bảo trì).


  - `/dsnguoidung`: Xem danh sách tất cả Telegram ID đã sử dụng bot.
  - `/thongbao <nội dung>`: Gửi thông báo broadcast an toàn tới toàn bộ người dùng, tự động bắt lỗi blocked/forbidden.
- **Sẵn sàng cho Production:** Hỗ trợ Docker (non-root), Docker Compose, Systemd Service và Rotating File Logging.

---

## 📁 CẤU TRÚC PROJECT

```text
cloudphonefree_bot/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Khởi tạo Telegram Application và đăng ký handler
│   ├── config.py                # Pydantic Settings đọc và validate .env
│   ├── logging_config.py        # Rotating file & console logging
│   ├── dependencies.py          # Dependency injection container
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py        # Quản lý kết nối SQLite async (aiosqlite)
│   │   ├── models.py            # Data models
│   │   └── repositories.py      # Thao tác User, Account, PendingSession
│   ├── services/
│   │   ├── __init__.py
│   │   ├── api_client.py        # Base HTTP async client (httpx) có retry & timeout
│   │   ├── mail_service.py      # Tương tác API mail.tm (tạo mail, lấy OTP)
│   │   ├── willclouds_service.py# Tương tác API WillClouds/UmoCloud
│   │   └── account_service.py   # Điều phối tạo tài khoản & đặt mật khẩu
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py             # Lệnh /start, /id
│   │   ├── admin.py             # Lệnh admin (/thongke, /dsnguoidung, /thongbao)
│   │   ├── callback.py          # Callback create_account, trial_yes, trial_no
│   │   └── errors.py            # Global error handler
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── inline.py            # Inline keyboards
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── rate_limit.py        # Cooldown rate limiter
│   └── utils/
│       ├── __init__.py
│       ├── crypto.py            # java_url_encode, sign MD5, RSA encryption
│       ├── helpers.py           # Escape HTML, format output
│       └── validators.py        # Validate dữ liệu
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_crypto.py
│   ├── test_services.py
│   └── test_validators.py
├── data/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── run.py
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY LOCAL

### Yêu cầu:
- Python 3.12 trở lên.

### Trên Windows (PowerShell):

```powershell
# 1. Tạo môi trường ảo
python -m venv .venv

# 2. Kích hoạt môi trường ảo
.venv\Scripts\Activate.ps1

# 3. Cài đặt thư viện
pip install -r requirements.txt

# 4. Tạo file cấu hình từ file mẫu
copy .env.example .env

# 5. Mở file .env và điền BOT_TOKEN mới từ @BotFather cùng ADMIN_IDS

# 6. Build Frontend (nếu chưa có thư mục static/dist)
cd frontend
npm install
npm run build
cd ..

# 7. Chạy bot
python run.py
```

### Trên Linux / MacOS (Bash):

```bash
# 1. Tạo môi trường ảo
python3 -m venv .venv

# 2. Kích hoạt môi trường ảo
source .venv/bin/activate

# 3. Cài đặt thư viện
pip install -r requirements.txt

# 4. Tạo file cấu hình
cp .env.example .env

# 5. Điền BOT_TOKEN và ADMIN_IDS vào file .env
nano .env

# 6. Build Frontend (nếu chưa có thư mục static/dist)
cd frontend
npm install
npm run build
cd ..

# 7. Chạy bot
python run.py
```

---

## 🧪 CHẠY KIỂM THỬ (TESTS)

```bash
python -m pytest -v
```

---

## 🐳 TRIỂN KHAI BẰNG DOCKER & DOCKER COMPOSE

```bash
# 1. Tạo file .env và điền token
cp .env.example .env

# 2. Khởi chạy bot nền với Docker Compose
docker compose up -d --build

# 3. Xem log thời gian thực
docker compose logs -f bot

# 4. Dừng bot
docker compose down
```

---

## 🛡️ TRIỂN KHAI TRÊN VPS (SYSTEMD SERVICE)

Tạo file service tại `/etc/systemd/system/cloudphone_bot.service`:

```ini
[Unit]
Description=CloudPhone Free Telegram Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cloudphonefree_bot
ExecStart=/opt/cloudphonefree_bot/.venv/bin/python run.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/cloudphonefree_bot/logs/systemd.log
StandardError=append:/opt/cloudphonefree_bot/logs/systemd_error.log
EnvironmentFile=/opt/cloudphonefree_bot/.env

[Install]
WantedBy=multi-user.target
```

Kích hoạt và chạy service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudphone_bot
sudo systemctl start cloudphone_bot
sudo systemctl status cloudphone_bot
```

---

## 📋 CHECKLIST TRƯỚC KHI ĐƯA LÊN PRODUCTION

- [x] **Thu hồi token cũ:** Vào `@BotFather`, gõ `/revoke` và dán token mới vào `.env`.
- [x] **Phân quyền Admin:** Đảm bảo `ADMIN_IDS` trong `.env` chứa đúng Telegram ID của bạn (dùng lệnh `/id` trên bot để lấy).
- [x] **Bảo vệ File Secret:** Kiểm tra `.gitignore` để đảm bảo `.env`, thư mục `data/` và `logs/` không bị đẩy lên GitHub/GitLab.
- [x] **Chạy Unit Test:** Toàn bộ 13/13 test cases đều passed.
- [x] **Thử nghiệm tải và lỗi mạng:** Đã có cơ chế retry tự động với Exponential Backoff khi API bên thứ ba gặp sự cố.
