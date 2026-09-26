# Hệ Thống Quản Lý Cho Thuê Phòng Trọ & Căn Hộ
**Dự án Thực tập Chuyên sâu — Nhóm TTCS_T926_K12C3_N1**

---

## Phiên bản Spring Boot + React

Nhánh `feature/tenant-self-registration-spring-react` triển khai lại chức năng
đăng ký khách thuê theo stack trong yêu cầu ban đầu:

- Backend: Spring Boot 3, Java 17, Spring Data JPA, PostgreSQL 15.
- Frontend: React 18, TypeScript, Vite.
- Xác thực: BCrypt, JWT access token 30 phút và refresh token 7 ngày.

### Trạng thái bàn giao

- [x] Lát 1: đăng ký khách thuê, hash BCrypt, JWT access/refresh token và tự động đăng nhập.
- [x] Lát 2: kiểm tra trùng email/số điện thoại, trả lỗi đúng field với HTTP `409`.
- [x] Đăng nhập bằng email hoặc số điện thoại.
- [x] Frontend hiển thị nhãn vai trò `Khách thuê`, không hiển thị mã `TENANT`.
- [x] Backend integration tests và frontend production build đã pass.

Nhánh này đã push lên GitHub nhưng **chưa merge vào `dev`**. Các thay đổi cũ
trên nhánh `feature/tenant-self-registration` vẫn được giữ nguyên.

### Chạy nhanh trên Windows

Yêu cầu: Docker Desktop đang mở, Java 17, Maven 3.9+ và Node.js 20+.
Các đường dẫn Java/Maven dưới đây là vị trí trên máy phát triển hiện tại; nếu
máy khác cài ở nơi khác thì sửa `JAVA_HOME` và `Path` tương ứng.

Mở PowerShell thứ nhất tại thư mục gốc repository:

```powershell
docker compose up -d postgres
$env:JAVA_HOME = "D:\DevTools\Java\temurin-17.0.20.1+1"
$env:MAVEN_OPTS = "-Dmaven.repo.local=D:\DevCache\m2"
$env:Path = "D:\DevTools\Maven\apache-maven-3.9.9\bin;$env:Path"
Set-Location backend
mvn test
mvn spring-boot:run
```

Mở PowerShell thứ hai tại thư mục gốc repository:

```powershell
Set-Location frontend
npm install
npm run dev -- --host 127.0.0.1
```

Mở URL Vite được in trong terminal, thường là `http://127.0.0.1:5173/`.
Nếu cổng đó đang bận, Vite sẽ chọn cổng tiếp theo, thường là `5174`.

### Các lệnh riêng

Chạy PostgreSQL (Docker Engine phải đang chạy):

```powershell
docker compose up -d postgres
```

Chạy backend test bằng H2, không cần PostgreSQL:

```powershell
Set-Location backend
mvn test
```

Backend chạy tại `http://localhost:8080`.

API đăng ký:

```text
POST http://localhost:8080/api/auth/register
```

Body JSON:

```json
{
  "fullName": "Nguyen Van A",
  "phone": "0901234567",
  "email": "a@example.com",
  "password": "MatKhau123"
}
```

API đăng nhập bằng email hoặc số điện thoại:

```text
POST http://localhost:8080/api/auth/login
```

```json
{
  "identifier": "a@example.com",
  "password": "MatKhau123"
}
```

Sai thông tin đăng nhập trả HTTP `401` với mã `INVALID_CREDENTIALS`.

Lỗi validation trả HTTP `400` với `fieldErrors`. Lỗi trùng email hoặc số điện
thoại trả HTTP `409` với mã `DUPLICATE_FIELD`; frontend hiển thị lỗi đúng tại
field tương ứng và không tạo tài khoản mới.

Kiểm tra backend bằng H2 test database, không cần PostgreSQL:

```powershell
cd backend
mvn test
```

Để dừng PostgreSQL sau khi demo:

```powershell
docker compose down
```

---

