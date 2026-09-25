# Hệ Thống Quản Lý Cho Thuê Phòng Trọ & Căn Hộ
**Dự án Thực tập Chuyên sâu — Nhóm TTCS_T926_K12C3_N1**

---

## 1. Công nghệ sử dụng
- **Ngôn ngữ**: Python 3.12+
- **Framework**: Django 5.1
- **Cơ sở dữ liệu**: SQLite (bảng nghiệp vụ theo thiết kế `docs/02-csdl.md`)
- **Giao diện**: Django Templates, HTML5, CSS3, JavaScript, Bootstrap 5.3
- **Bảo mật**: Django Session, CSRF Protection, Password Hasher `BCryptSHA256PasswordHasher` (thư viện `bcrypt`).

---

## 2. Hướng dẫn cài đặt và khởi chạy

### Bước 1: Chuẩn bị môi trường ảo
```powershell
# Tạo môi trường ảo Python
py -3.12 -m venv .venv

# Kích hoạt môi trường ảo (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
```

### Bước 2: Cài đặt các gói phụ thuộc
```powershell
pip install -r requirements.txt
```

### Bước 3: Thực hiện di chuyển cơ sở dữ liệu (Migration)
```powershell
python manage.py migrate
```

### Bước 4: Chạy kiểm thử tự động (36 test cases)
```powershell
python manage.py test accounts -v 2
```

### Bước 5: Khởi động máy chủ phát triển
```powershell
python manage.py runserver
```
Truy cập trình duyệt tại:
- Trang đăng ký tài khoản khách thuê: `http://127.0.0.1:8000/dang-ky/` hoặc `http://127.0.0.1:8000/`
- Trang đăng nhập: `http://127.0.0.1:8000/dang-nhap/`
- Trang chủ / Dashboard: `http://127.0.0.1:8000/trang-chu/`
- Trang quản trị: `http://127.0.0.1:8000/admin/`

### Demo API đăng ký

Gửi request `POST` tới `http://127.0.0.1:8000/api/auth/register/` với header
`Content-Type: application/json`:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/auth/register/ `
  -ContentType 'application/json' `
  -Body '{"ho_ten":"Nguyen Van A","so_dien_thoai":"0901234567","email":"a@example.com","mat_khau":"MatKhau123"}'
```

Request hợp lệ trả về HTTP `201`, thông tin tài khoản, `access_token` và
`refresh_token`. Có thể dùng access token để gọi API thông tin tài khoản:

```powershell
$response = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/auth/register/ `
  -ContentType 'application/json' `
  -Body '{"ho_ten":"Nguyen Van B","so_dien_thoai":"0901234568","email":"b@example.com","mat_khau":"MatKhau123"}'

Invoke-RestMethod `
  -Method Get `
  -Uri http://127.0.0.1:8000/api/auth/me/ `
  -Headers @{ Authorization = "Bearer $($response.tokens.access_token)" }
```

Nếu dữ liệu không hợp lệ, API trả HTTP `400` và lỗi theo từng trường trong
`field_errors`.

---

## 3. Trạng thái tính năng hiện tại (Sprint 1)
- **S1-01: Đăng ký tài khoản Khách thuê**:
  - [x] Task 1: Biểu mẫu đăng ký 4 trường, kiểm tra định dạng số điện thoại (10 chữ số bắt đầu bằng 0), mật khẩu (>=8 ký tự, có chữ và số), băm BCrypt, tự động đăng nhập và chuyển hướng trang đích.
  - [x] Task 2: Ngăn trùng lặp số điện thoại và email độc lập, hiển thị lỗi đúng trường, xử lý bắt lỗi xung đột DB `IntegrityError`.