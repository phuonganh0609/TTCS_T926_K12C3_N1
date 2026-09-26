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
- S1-01 chưa tạo hồ sơ lúc đăng ký. Từ S1-06, hồ sơ `khach_thue` được tạo khi khách thuê lưu trang hồ sơ lần đầu.

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
- **S1-06**: Hoàn thành cả ba lát: thông tin/căn cước, ảnh hai mặt, phân quyền hiển thị căn cước theo vai trò và quan hệ phòng đang thuê.
- **S1-07 đến S1-10**: Khai báo danh mục tòa nhà, phòng trọ, bảng giá dịch vụ và nhật ký thao tác.

## 5. S1-06 — Thông tin hồ sơ cá nhân (2026-09-26)

- Hoàn thành GET/POST `/ho-so/`, có mục “Hồ sơ cá nhân” trong menu khách thuê.
- Model `KhachThue`, bảng `khach_thue`, migration `0003_khachthue`: một hồ sơ/tài khoản, họ tên, ngày sinh, số căn cước (`so_giay_to`), quê quán, nghề nghiệp và ngày tạo.
- Chỉ tài khoản KHACH_THUE đang đăng nhập được xem/lưu hồ sơ của chính mình; không nhận ID chủ hồ sơ từ client. POST có CSRF, trang hồ sơ có `Cache-Control: no-store`.
- Căn cước là chuỗi 9 hoặc 12 chữ số ASCII, giữ số 0 đầu; từ chối chữ, ký tự đặc biệt, khoảng trắng và mọi độ dài khác. Kiểm tra backend độc lập với JavaScript; lỗi ngay dưới trường khi nhập, blur hoặc submit.
- Lưu thành công chuyển lại trang hồ sơ, thông báo thành công và hiển thị dữ liệu đã lưu. Cập nhật giữ nguyên bản ghi; dữ liệu sai không ghi đè hồ sơ cũ.
- Giả định: cả 5 trường bắt buộc; quê quán là trường riêng, không đồng nhất địa chỉ thường trú; họ tên hồ sơ độc lập họ tên tài khoản, chỉ lấy tên tài khoản làm gợi ý lần đầu. Không đặt UNIQUE cho căn cước khi chưa có yêu cầu.
- Phạm vi task 1: số căn cước dạng chuỗi trong SQLite, chưa mã hóa ở tầng ứng dụng; mô hình tổng thể có định hướng mã hóa để triển khai riêng. Ảnh được bổ sung trong task 2, che số theo quyền ở task 3 bên dưới. Chưa triển khai hồ sơ người ở ghép hay API JSON hồ sơ.

- Đã chạy `python manage.py test accounts -v 1`: **45/45 passed**, gồm 12 test mới tại `accounts/test_profile.py`; kiểm tra ranh giới căn cước, lưu/sửa/mở lại, ngày sai, bắt buộc trường, chủ sở hữu, vai trò và CSRF.
- Đã chạy `makemigrations --check --dry-run`: không thiếu migration; đã áp dụng `0003_khachthue` vào CSDL hiện tại.
- Đã kiểm tra tương tác trong Browser bằng tài khoản giả và CSDL thử nghiệm trong bộ nhớ: lỗi căn cước có chữ hiện ngay khi nhập; lưu 9 chữ số, cập nhật 12 chữ số và nghề nghiệp, tải lại vẫn giữ dữ liệu. Chưa xác minh trực quan bằng ảnh chụp hoặc kích thước mobile (công cụ chụp ảnh không trả ảnh).

## 6. S1-06 task 2 — Ảnh giấy tờ (2026-09-26)

- Migration `0004` bổ sung ảnh mặt trước/mặt sau; dùng Pillow 12.0.0 kiểm tra nội dung JPEG/PNG, giới hạn mỗi tệp 5MB, thu nhỏ chiều rộng tối đa 1600px theo đúng tỷ lệ và bỏ metadata.
- Form có chọn ảnh, xem trước, báo lỗi từng mặt, hiển thị lại ảnh đã lưu và thay thế riêng từng mặt. Có thể bổ sung ảnh sau khi đã lưu thông tin.
- Lưu riêng tại `private_media/`; route ảnh yêu cầu session và đúng chủ hồ sơ. Không có URL media công khai. Khi thay ảnh, dọn ảnh cũ sau commit; khi lỗi CSDL, dọn ảnh mới.
- `python manage.py test accounts -v 1`: **57/57 passed**, gồm 12 test ảnh mới (JPEG/PNG, hai mặt, 5MB và trên 5MB, 1600px và hai phía ngưỡng, tệp giả/hỏng, thay ảnh, giữ ảnh khi sửa chữ, quyền truy cập, rollback khi lưu lỗi).
- Đã chạy `makemigrations --check --dry-run`: không thiếu migration; `migrate` áp dụng `0004` thành công, bảo toàn hồ sơ cũ.
- Browser: đã chọn JPG và PNG, xác nhận hai ảnh xem trước, lưu và tải lại thấy đủ hai ảnh. Kích thước ảnh được phục vụ: JPG 2400×1500 thành 1600×1000; PNG 800×500 giữ nguyên. Dùng tài khoản/CSDL thử riêng, không ghi dữ liệu giả vào CSDL của người dùng.
- Tại thời điểm task 2 chưa che số căn cước; task 3 bên dưới đã bổ sung quyền cho ADMIN/chủ nhà đúng phòng và bảo vệ ảnh trước người xem dạng che khác.
- Cảnh báo cấu hình có sẵn: `staticfiles.W004` do thư mục `static` chưa tồn tại.

## 7. S1-06 task 3 — Phân quyền căn cước (2026-09-26)

- **PO đã chốt:** 9 số `*****6789`, 12 số `********6789`; thay từng số bị che bằng dấu *, chỉ giữ 4 số cuối.
- ADMIN được xem đầy đủ. CHU_NHA được xem đầy đủ khi đúng chủ tòa của phòng trong hợp đồng `DANG_HIEU_LUC` của khách, có một kỳ chứa hôm nay và chưa trả phòng trước hôm nay. Mọi vai trò khác (kể cả chính khách thuê) chỉ thấy dạng che. `is_staff`/`is_superuser` không thay vai trò nghiệp vụ.
- Bổ sung 4 model quan hệ tối thiểu `ToaNha`, `PhongTro`, `HopDong`, `KyHopDong` theo DBML qua migration `0005`. Django Admin cho quản trị được cấp quyền thiết lập quan hệ để demo; không mở CRUD quan hệ cho khách/chủ nhà/quản lý và không triển khai toàn bộ nghiệp vụ cho thuê.
- Trang xem `/ho-so/<id>/` chỉ nhận dictionary đã phân quyền từ `profile_permissions.py`, không nhận model chứa số đầy đủ. Danh sách `/ho-so/khach-thue/` dành cho ADMIN/CHU_NHA/QUAN_LY chỉ có tên/liên kết. Trang xem cho tài khoản đã đăng nhập xem các trường thông thường và số đã phân quyền theo AC; chưa đăng nhập được chuyển tới đăng nhập.
- Trang sửa `/ho-so/` không prefill hoặc echo căn cước, kể cả khi POST lỗi. Ô trống giữ số cũ; số mới vẫn phải đúng 9/12 chữ số. Không có số đầy đủ trong HTML/hidden/data attribute/JavaScript gửi về người bị che.
- Ảnh của chính khách thuê vẫn xem/sửa bình thường. ADMIN/chủ nhà đúng phòng xem ảnh qua endpoint kiểm tra quyền; người không liên quan nhận 403 cả khi biết URL ảnh. Ảnh gốc của chính khách thuê có thể chứa căn cước như trước; không thêm OCR/che ảnh.
- **Kiểm thử: 76/76 passed** với `python manage.py test accounts -v 1`, gồm 19 test quyền mới; ma trận vai trò × 9/12 số, hợp đồng hết hạn/tương lai/nháp/hủy/trả sớm, biên ngày, đổi chủ tòa, chống giả tham số, bảo toàn căn cước khi sửa, chặn ảnh và hồi quy hai lát trước.
- Browser với dữ liệu giả trong CSDL riêng: đã đối chiếu hai hồ sơ 9/12 số qua khách thuê, chủ nhà đúng phòng, chủ nhà khác, quản lý và ADMIN; số và quyền hiển thị ảnh đúng ma trận.
- Browser trang sửa: HTML không chứa số căn cước đầy đủ, input không có value cũ; để trống căn cước rồi sửa nghề nghiệp vẫn lưu thành công, mở trang xem giữ đúng 4 số cuối.
- Đã chạy `makemigrations --check --dry-run`: không thiếu migration; đã áp dụng `0005` vào CSDL hiện tại. Không reset dữ liệu, không thay đổi index Git đang được stage từ các lát trước.
- Các trường nghiệp vụ chưa có của tòa/phòng/hợp đồng, hồ sơ người ở ghép và quy trình hợp đồng đầy đủ thuộc story sau; không còn AC chưa triển khai trong ba lát S1-06 đã giao.
