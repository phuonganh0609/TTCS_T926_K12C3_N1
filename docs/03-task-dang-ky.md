# Task hiện tại: S1-01 — Đăng ký tài khoản khách thuê

## Phạm vi

Từ dự án chưa có mã, triển khai hai phần dưới đây bằng Django, Django Templates, Bootstrap 5 và SQLite.
Đọc 00-huong-dan.md và bảng tai_khoan trong 02-csdl.md trước khi lập trình.
Đây là chỉ dẫn task trực tiếp được tổng hợp từ yêu cầu người dùng, không phải toàn bộ backlog cần làm ngay.

## Task 1 — Tạo tài khoản hợp lệ và tự đăng nhập

- Biểu mẫu bốn trường: họ tên, số điện thoại, email, mật khẩu.
- Số điện thoại đúng 10 chữ số ASCII, bắt đầu bằng 0.
- Email đúng định dạng.
- Mật khẩu ít nhất 8 ký tự, có ít nhất một chữ cái và một chữ số.
- Băm bằng BCrypt thông qua hasher Django; dùng BCryptSHA256PasswordHasher và set_password/check_password.
- Không lưu/log mật khẩu rõ; không tự trim hoặc thay đổi mật khẩu.
- Tạo tài khoản, gán KHACH_THUE ở backend; không nhận role/staff/superuser từ form.
- Sau lưu thành công, tạo phiên đăng nhập, hiện thông báo thành công và chuyển tới trang trong ứng dụng.
- Nếu chưa có trang đích: tạo một trang chỉ người đã đăng nhập được xem, hiển thị họ tên và vai trò.

## Task 2 — Ngăn trùng điện thoại/email

- Kiểm tra độc lập số điện thoại và email đã tồn tại.
- Trùng trường nào báo dưới trường đó; trùng cả hai hiện cả hai lỗi trong một lần gửi.
- Không tạo tài khoản hoặc phiên đăng nhập mới khi bị từ chối.
- Chuẩn hóa email strip/lowercase nhất quán; điện thoại strip đầu/cuối, giữ dạng chuỗi.
- UNIQUE ở DB là bảo vệ cuối; kiểm tra exists() đơn thuần không đủ khi có hai request đồng thời.
- Xử lý IntegrityError ngoài transaction lỗi đúng cách, kiểm tra xung đột đã biết và không trả trang 500
  cho lỗi trùng bình thường. Không biến mọi lỗi DB thành lỗi email trùng.
- Có thể đặt unique ngay từ nền tảng Task 1; Task 2 hoàn thiện thông báo thân thiện và các ca kiểm thử.

## Mặc định giao diện cần ghi nhận là giả định, chưa phải PO đã duyệt

- Lỗi định dạng hiển thị khi rời trường và khi bấm gửi; backend luôn kiểm tra lại.
- Trùng cả email/điện thoại: hai thông báo riêng dưới hai trường.
- Khi lỗi giữ họ tên, email, điện thoại; không điền lại mật khẩu.
- Thông báo: “Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0.”
- Thông báo: “Mật khẩu phải có ít nhất 8 ký tự, gồm ít nhất một chữ cái và một chữ số.”
- Thông báo: “Số điện thoại này đã được sử dụng.” / “Email này đã được sử dụng.”
- Thành công: “Đăng ký thành công.”

## Nền tảng và giới hạn

- Chọn phiên bản Python/Django tương thích và cố định thư viện; ghi README.
- Custom User trước migrate đầu tiên; dùng mật khẩu/session/CSRF chuẩn Django.
- Ánh xạ db_table=tai_khoan, password vào cột mat_khau, is_active vào dang_hoat_dong khi phù hợp.
- Thêm trường kỹ thuật do Django cần thì ghi rõ; không xây hai hệ tài khoản độc lập.
- Hồ sơ khach_thue có thể để giai đoạn sau; nếu tạo cùng tài khoản phải atomic.
- Không cần triển khai toàn bộ 22 bảng, JWT, OTP, quên mật khẩu, đăng nhập bằng nhiều định danh,
  khóa đăng nhập sai, dashboard đầy đủ hoặc nghiệp vụ cho thuê trong lần này.
- Chỉ lấy các thành phần hiện có thực sự cần cho task; không tự mở rộng phạm vi.

## Kiểm thử và demo

1. Đăng ký hợp lệ tạo đúng một user, role KHACH_THUE, tự đăng nhập và chuyển đúng trang.
2. Điện thoại thiếu/thừa số, không bắt đầu bằng 0, có ký tự sai đều bị từ chối.
3. Mật khẩu dưới 8 ký tự, thiếu chữ, thiếu số đều bị từ chối.
4. Mật khẩu trong DB không phải rõ; check_password thành công; hasher đúng BCrypt đã cấu hình.
5. Trùng điện thoại báo đúng trường, số lượng user không tăng.
6. Trùng email báo đúng trường, số lượng user không tăng.
7. Trùng cả hai hiện đủ hai lỗi.
8. Email khác hoa/thường nhưng cùng giá trị chuẩn hóa bị coi là trùng.
9. Gửi thêm vai trò ADMIN/is_staff/is_superuser không nâng quyền được.
10. Bỏ qua JavaScript vẫn bị backend kiểm tra.
11. Đăng ký thất bại không tạo dữ liệu dở dang/phiên mới.
12. Dữ liệu hoàn toàn mới tiếp tục hoạt động sau khi thêm kiểm tra trùng.
13. Kiểm tra CSRF và trang đích yêu cầu đăng nhập.
14. Kiểm tra giao diện trên màn hình điện thoại và máy tính.

Demo lần lượt Task 1 rồi Task 2. Chạy tests, sửa lỗi, bàn giao README/cách chạy/migrations và kết quả thật.
Không chỉ đưa kế hoạch hoặc đoạn code rời; thực hiện trong thư mục dự án đang mở.
