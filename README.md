# Hệ Thống Quản Lý Cho Thuê Phòng Trọ & Căn Hộ
**Dự án Thực tập Chuyên sâu — Nhóm TTCS_T926_K12C3_N1**

---

## 🛠️ Công Nghệ Sử Dụng (Nhánh chính `dev`)

- **Backend**: Spring Boot 3, Java 17, Spring Data JPA, Spring Security 6.
- **Frontend**: React 18, TypeScript, Vite, Lucide Icons.
- **Database**: PostgreSQL 15 (Chạy qua Docker), H2 Database (cho Integration Tests).
- **Xác thực & Bảo mật**: BCrypt password hashing, JWT Access Token (30 phút) & Refresh Token (7 ngày) lưu DB, Token Revocation (Blacklist) khi Đăng xuất.

---

## 🚀 Hướng Dẫn Chạy Nhanh Cho Đồng Đội (Windows)

### Yêu cầu cài đặt trước:
1. **Docker Desktop** đang bật.
2. **Java 17** & **Maven 3.9+**.
3. **Node.js 20+** & **npm 10+**.

---

### Bước 1: Khởi động CSDL PostgreSQL (Docker)
Mở PowerShell tại thư mục gốc repository:
```powershell
docker compose up -d postgres
```

### Bước 2: Khởi chạy Backend Spring Boot (Port 8080)
Mở PowerShell thứ nhất:
```powershell
# Nạp biến môi trường Java 17 / Maven (nếu chưa cài sẵn vào System Path)
$env:JAVA_HOME = "D:\DevTools\Java\temurin-17.0.20.1+1"
$env:Path = "$env:JAVA_HOME\bin;D:\DevTools\Maven\apache-maven-3.9.9\bin;$env:Path"

# Vào thư mục backend và chạy
cd backend
mvn test
mvn spring-boot:run
```
Backend API sẽ chạy tại: `http://localhost:8080`

### Bước 3: Khởi chạy Frontend React Vite (Port 5173)
Mở PowerShell thứ hai:
```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```
Mở trình duyệt truy cập: `http://127.0.0.1:5173/`

---

## 📋 Danh Sách Tính Năng Đã Tích Hợp (Sprint 1)

### 1. S1-01: Đăng Ký Tài Khoản Khách Thue
- Form đăng ký 4 trường (`fullName`, `phone`, `email`, `password`).
- Mã hoá BCrypt, sinh JWT Token tự động đăng nhập sau khi tạo tài khoản.
- Validation dữ liệu: Số điện thoại (10 chữ số bắt đầu bằng 0), Mật khẩu (>=8 ký tự, có chữ & số).
- Bắt trùng Email/SĐT độc lập: trả HTTP `409 CONFLICT` mã `DUPLICATE_FIELD` và highlight đúng khung nhập trên UI.

### 2. S1-02: Đăng Nhập & Bảo Vệ Phiên Làm Việc
- Đăng nhập bằng **Email HOẶC Số điện thoại**.
- **Chống dò mật khẩu**: Nhập sai 5 lần liên tiếp trong 15 phút → Tạm khóa tài khoản 15 phút (trả HTTP `423`).
- **Đăng xuất & Vô hiệu hóa phiên**: Endpoint `/api/auth/logout` đưa Access Token vào Blacklist và vô hiệu hóa Refresh Token trong DB.
- **Refresh Token Rotation**: Endpoint `/api/auth/refresh` cấp lại Access Token mới.

### 3. S1-06: Hồ Sơ Cá Nhân Khách Thuê & Phân Quyền Giấy Tờ
- Form khai báo hồ sơ: Họ tên, Ngày sinh, Số Căn cước (CCCD), Quê quán, Nghề nghiệp.
- **Bảo mật Căn cước**: Che tự động (`*****6789` với 9 số, `********6789` với 12 số) để bảo vệ quyền riêng tư.
- **Upload Ảnh Giấy Tờ**: Tải lên ảnh mặt trước/sau (tối đa 5MB, định dạng JPG/PNG). Tự động thu nhỏ chiều rộng ảnh nếu vượt quá 1600px để tối ưu lưu trữ.

---

## 🧪 Chạy Kiểm Thử Tự Động (Backend Tests)

Để kiểm tra toàn bộ 11 Integration & Unit test cases:
```powershell
cd backend
mvn test
```

---

## 🛑 Dừng Các Dịch Vụ Sau Khi Test

```powershell
docker compose down
```
