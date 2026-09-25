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

### Bước 4: Chạy kiểm thử tự động (76 test cases)
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
- Hồ sơ cá nhân khách thuê: `http://127.0.0.1:8000/ho-so/` (cần đăng nhập).
- Danh sách hồ sơ cho ADMIN/CHU_NHA/QUAN_LY: `http://127.0.0.1:8000/ho-so/khach-thue/`; trang xem `/ho-so/<id>/` trả căn cước theo quyền.
- Trang quản trị: `http://127.0.0.1:8000/admin/`

---

## 3. Trạng thái tính năng hiện tại (Sprint 1)
- **S1-01: Đăng ký tài khoản Khách thuê**:
  - [x] Task 1: Biểu mẫu đăng ký 4 trường, kiểm tra định dạng số điện thoại (10 chữ số bắt đầu bằng 0), mật khẩu (>=8 ký tự, có chữ và số), băm BCrypt, tự động đăng nhập và chuyển hướng trang đích.
  - [x] Task 2: Ngăn trùng lặp số điện thoại và email độc lập, hiển thị lỗi đúng trường, xử lý bắt lỗi xung đột DB `IntegrityError`.

- **S1-06: Thông tin hồ sơ cá nhân**:
  - [x] Xem, lưu mới, cập nhật và mở lại họ tên, ngày sinh, căn cước, quê quán, nghề nghiệp.
  - [x] Căn cước đúng 9 hoặc 12 chữ số, giữ số 0 đầu; báo lỗi ngay tại trường ở giao diện và backend.
  - [x] Chỉ khách thuê sửa hồ sơ của mình; CSRF và kiểm thử quyền truy cập.
  - [x] Tải, xem trước, lưu và thay thế ảnh mặt trước/mặt sau: JPG/JPEG hoặc PNG, tối đa 5 × 1024 × 1024 byte mỗi ảnh; tự thu nhỏ chiều rộng trên 1600px, giữ tỷ lệ.
  - Ảnh nằm trong `private_media/`, không đưa vào Git; chỉ chủ hồ sơ, ADMIN hoặc đúng chủ nhà đang cho thuê đọc được qua view kiểm tra quyền. Không cấu hình web server phục vụ công khai thư mục này. Sao lưu thư mục ảnh cùng CSDL.
  - [x] Căn cước 9 số che `*****6789`, 12 số che `********6789`; chỉ ADMIN và đúng chủ nhà của phòng đang thuê xem đầy đủ. Trang sửa không điền lại căn cước: để trống giữ số cũ, nhập mới để thay.
  - Xem `docs/03-task-ho-so.md` để tạo quan hệ thuê qua Django Admin và demo tất cả vai trò. Các bảng quan hệ thuê hiện chỉ có phần tối thiểu phục vụ quyền S1-06.
  - Khi cập nhật mã nguồn, cài `pip install -r requirements.txt`, chạy `python manage.py migrate` (hồ sơ `0003`, ảnh `0004`, quan hệ thuê `0005`).
