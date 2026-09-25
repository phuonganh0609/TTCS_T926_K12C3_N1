# Báo Cáo Tiến Độ Triển Khai

## 1. Phạm vi đã hoàn thành
- **Story S1-01: Đăng ký tài khoản Khách thuê**:
  - **Task 1: Tạo tài khoản hợp lệ và tự đăng nhập**:
    - Thiết lập nền tảng dự án Django 5.1 với SQLite và Custom User model `TaiKhoan` (bảng `tai_khoan` trong CSDL, ánh xạ `mat_khau` và `dang_hoat_dong`).
    - Cấu hình Password Hasher `BCryptSHA256PasswordHasher` (thư viện `bcrypt`). Mật khẩu không lưu dạng thô trong DB và không log.
    - Biểu mẫu 4 trường: Họ tên, Số điện thoại, Email, Mật khẩu.
    - Kiểm tra số điện thoại: đúng 10 chữ số ASCII và bắt đầu bằng số 0 (`^0[0-9]{9}$`).
    - Kiểm tra mật khẩu: tối thiểu 8 ký tự, có ít nhất một chữ cái và một chữ số.
    - Gán vai trò mặc định `KHACH_THUE` ở tầng backend, ngăn chặn hành vi giả mạo nâng quyền `is_staff` / `is_superuser` / `vai_tro`.
    - Tự động đăng nhập người dùng bằng Django session ngay sau khi lưu tài khoản thành công, gửi flash message thành công và chuyển hướng tới trang đích (`/trang-chu/`).
    - Xây dựng trang đích (`dashboard`) bảo vệ bằng `@login_required`, hiển thị lời chào, họ tên và vai trò người dùng.
    - Giao diện thân thiện bằng Bootstrap 5.3, tương thích tốt trên màn hình máy tính và thiết bị di động (từ 360px).
    - Hỗ trợ client-side validation khi rời trường (blur) và khi bấm gửi (submit), kết hợp backend validation độc lập.
  - **Task 2: Ngăn trùng điện thoại / email và báo rõ trường bị trùng**:
    - Kiểm tra độc lập sự tồn tại của số điện thoại và email trong CSDL.
    - Báo lỗi đúng vị trí trường bị trùng; trường hợp trùng cả hai hiển thị đồng thời cả hai lỗi trong một lần gửi form.
    - Chuẩn hóa email `strip().lower()` nhất quán trước khi kiểm tra và lưu.
    - Giữ lại giá trị họ tên, số điện thoại, email trên biểu mẫu khi có lỗi; không tự động điền lại mật khẩu.
    - Bọc logic lưu dữ liệu trong `transaction.atomic()` và bắt `IntegrityError` ở mức database để xử lý tranh chấp đồng thời mà không làm sập ứng dụng (không trả lỗi 500).
  - **Kiểm thử tự động**:
    - Viết bộ kiểm thử gồm 14 test cases tại `accounts/tests.py`, bao quát 100% các tiêu chí chấp nhận và kịch bản biên trong tài liệu `03-task-dang-ky.md`.
    - Kết quả: **14/14 test cases passed**.

## 2. Giả định ghi nhận
- Giao diện người dùng sử dụng Bootstrap 5.3 CDN và Bootstrap Icons để đảm bảo giao diện responsive từ 360px mà không cần bundle tool phức tạp.
- Thông báo lỗi giao diện khi blur và submit sử dụng các câu văn thân thiện theo giả định trong `03-task-dang-ky.md`.
- Trang đích sau đăng nhập là `/trang-chu/` đóng vai trò dashboard tối thiểu cho khách thuê, hiển thị thông tin tài khoản và có nút đăng xuất.
- Chưa tạo hồ sơ trong bảng `khach_thue` (được để lại cho giai đoạn sau theo chỉ dẫn tại `00-huong-dan.md`).

## 3. S1-02 — Đăng nhập và duy trì phiên làm việc cho Khách thuê

- **Trạng thái: hoàn thành các AC đăng nhập, khóa tạm thời và đăng xuất**:
  - Đăng nhập bằng email/số điện thoại, token access 30 phút và refresh 7 ngày; cùng thông báo chung khi sai thông tin.
  - Tự khóa sau 5 lần sai trong 15 phút, hiển thị đếm ngược và reset khi mở khóa/đăng nhập thành công.
  - Đăng xuất thu hồi token, xóa cookie và kết thúc Django session.
  - Django session được giới hạn 7 ngày; khi mở dashboard, access token hết hạn sẽ tự refresh. Refresh token hết hạn/không hợp lệ sẽ kết thúc session và chuyển về đăng nhập.
  - Giao diện/luồng web lưu token trong cookie trình duyệt. API login/refresh cũng được cung cấp cho client.
  - **Chưa có**: khóa tài khoản quản trị và luồng đăng xuất chủ động qua API trên client ngoài giao diện Django.

## 4. Việc còn lại tiếp theo (Product Backlog)
- **S1-03**: Quản trị hệ thống tạo và khóa tài khoản cho Chủ nhà cùng Quản lý tòa nhà.
- **S1-04**: Phân quyền theo vai trò và ẩn hiện menu tương ứng.
- **S1-05**: Đổi mật khẩu và lấy lại mật khẩu khi quên.
- **S1-06**: Khai báo hồ sơ cá nhân (`khach_thue`) gồm CCCD và ảnh giấy tờ.
- **S1-07 đến S1-10**: Khai báo danh mục tòa nhà, phòng trọ, bảng giá dịch vụ và nhật ký thao tác.
