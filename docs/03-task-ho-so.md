# S1-06 — Thông tin hồ sơ cá nhân

Yêu cầu trực tiếp: khách thuê khai báo, lưu, sửa và mở lại hồ sơ gồm họ tên, ngày sinh, số căn cước, quê quán, nghề nghiệp và ảnh giấy tờ hai mặt. Task 1 triển khai thông tin/căn cước; task 2 bổ sung ảnh; task 3 phân quyền số căn cước theo vai trò và quan hệ phòng đang thuê.

## Tiêu chí và cách triển khai

- `/ho-so/` GET đọc hồ sơ hiện tại, POST kiểm tra và lưu mới/cập nhật. Chưa có hồ sơ thì gợi ý họ tên tài khoản; GET không tạo bản ghi.
- Năm trường bắt buộc khi tạo. Khi sửa, ô căn cước để trống nghĩa là giữ số cũ; nhập số mới thì phải hợp lệ. Ngày sinh là ngày hợp lệ; chưa thêm giới hạn tuổi. Họ tên tối đa 100, quê quán 255, nghề nghiệp 150 ký tự.
- Số căn cước chỉ nhận đúng 9 hoặc 12 chữ số ASCII; không trim, không ép kiểu số, không tự bỏ ký tự sai. Không kiểm tra mã vùng/ngày sinh trong căn cước và chưa yêu cầu duy nhất giữa các hồ sơ.
- Lỗi nằm ngay dưới trường căn cước, có trạng thái invalid và liên kết ARIA; JavaScript kiểm tra khi input/blur/submit, backend kiểm tra lại khi nhận POST.
- Mỗi tài khoản khách thuê chỉ chỉnh sửa hồ sơ của mình qua session; vai trò khác nhận 403 ở trang sửa. Không lấy ID tài khoản/hồ sơ từ POST hoặc query string. Trang xem riêng áp dụng quy tắc bên dưới.
- Lưu hợp lệ có thông báo và redirect GET; mở lại thấy dữ liệu theo quyền. Lưu lỗi giữ các trường thông thường nhưng không điền lại căn cước/ảnh mới và không thay đổi bản ghi cũ.

## Khác biệt với mô hình tổng thể

Chỉ triển khai các trường cần cho task trên bảng `khach_thue`. `que_quan` bổ sung riêng với `dia_chi_thuong_tru`; liên kết tài khoản bắt buộc trong phạm vi này. Số căn cước dùng tên cột `so_giay_to`, hiện lưu chuỗi tối đa 12 ký tự; chưa mã hóa tầng ứng dụng, chưa triển khai liên hệ và người ở ghép. Dạng che tính khi trả dữ liệu, không cần cột số rút gọn. Họ tên hồ sơ không tự cập nhật tên tài khoản. Hai cột ảnh lưu đường dẫn riêng, không lưu ảnh trong SQLite.

Task 3 thêm các trường tối thiểu của 4 bảng trong DBML: `toa_nha` (tên/chủ nhà), `phong_tro` (tòa/mã phòng), `hop_dong` (mã/phòng/khách đứng tên/trạng thái/ngày trả), `ky_hop_dong` (hợp đồng/thứ tự/ngày bắt đầu/ngày kết thúc). Chưa triển khai giá, cọc, hóa đơn, quy trình ký hoặc người ở ghép; quyền hiện tại dựa trên khách đứng tên hợp đồng. Không tạo bảng phân quyền thuê giả lập tách khỏi mô hình nguồn.

## Task 2 — Ảnh giấy tờ

- Form multipart có hai ô chọn ảnh, xem trước bằng URL tạm của trình duyệt; ảnh đã lưu hiển thị qua `/ho-so/anh/truoc/` và `/ho-so/anh/sau/`.
- Giả định 5MB = 5 × 1024 × 1024 byte, tính riêng từng tệp trước khi xử lý. Đúng giới hạn được chấp nhận. JPG bao gồm `.jpg` và `.jpeg`, không phân biệt hoa/thường.
- Backend kiểm tra đuôi, định dạng thực JPEG/PNG và khả năng giải mã đầy đủ; từ chối tệp hỏng, giả đuôi hoặc vượt giới hạn. Lỗi gắn đúng mặt trước/mặt sau; không lưu hồ sơ hay ảnh mới khi form lỗi.
- Pillow xoay theo EXIF, thu chiều rộng trên 1600px về 1600px và giữ tỷ lệ; không phóng ảnh nhỏ. Mã hóa lại ảnh, bỏ metadata; JPEG quality 85, PNG giữ định dạng PNG.
- Có thể lưu thông tin trước rồi bổ sung từng mặt. Khi không chọn tệp mới, ảnh cũ giữ nguyên; chọn mới thay từng mặt. Nếu POST bị lỗi phải chọn lại tệp mới do giới hạn bảo mật của trình duyệt.
- Đường dẫn ngẫu nhiên trong `private_media/giay-to/`; không có route media public. Chủ hồ sơ vẫn đọc được ảnh của mình; task 3 cho ADMIN và đúng chủ nhà đang cho thuê đọc ảnh. Người xem dạng che khác không có quyền ảnh để tránh lấy số đầy đủ từ ảnh gốc.
- Chỉ xóa ảnh bị thay sau commit CSDL; nếu lưu lỗi thì dọn tệp mới và giữ bản cũ.

Demo ảnh: chọn JPG rộng 2400px cho mặt trước và PNG cho mặt sau, kiểm tra xem trước, lưu, mở lại. Ảnh mặt trước lưu rộng 1600px. Chọn ảnh mới để thay một mặt; mặt kia giữ nguyên. Thử GIF/TXT, ảnh hỏng và ảnh trên 5MB tại từng ô để thấy lỗi.

## Demo

1. Đăng nhập khách thuê, chọn **Hồ sơ cá nhân**.
2. Điền đủ 5 trường, căn cước giả `012345678`, bấm **Lưu hồ sơ**; kiểm tra thông báo và dữ liệu hiển thị.
3. Đổi căn cước thành `001234567890`, sửa thông tin khác, lưu rồi mở lại trang.
4. Thử `12345678a`, `1234-6789`, 8/10/11/13 chữ số: lỗi ngay dưới trường; không lưu được.
5. Kiểm tra backend và hồi quy: `python manage.py test accounts -v 1`.

## Task 3 — Phân quyền số căn cước

PO đã xác nhận trong phiên 2026-09-26: **9 số `*****6789`; 12 số `********6789`** (mỗi số bị che thay bằng một dấu *, giữ nguyên 4 số cuối).

| Người đang xem | Số căn cước |
| --- | --- |
| Vai trò ADMIN, tài khoản hoạt động | Đầy đủ |
| CHU_NHA của tòa chứa phòng khách đang thuê | Đầy đủ |
| Khách thuê, kể cả chính chủ hồ sơ | Che, còn 4 số cuối |
| Chủ nhà khác, quản lý, người dùng khác đã đăng nhập | Che, còn 4 số cuối |
| Chưa đăng nhập | Chuyển tới đăng nhập |

- “Đang thuê”: hợp đồng của đúng khách đứng tên có trạng thái `DANG_HIEU_LUC`; cùng một kỳ có bắt đầu ≤ ngày hiện tại ≤ kết thúc; ngày trả phòng NULL hoặc ≥ ngày hiện tại. Ngày tính theo Asia/Ho_Chi_Minh, bao gồm cả hai đầu theo DBML. Nháp/chờ hiệu lực/hết hạn/kết thúc/hủy hoặc đã trả sớm đều không cấp quyền. Quyền được tính lại mỗi request theo chủ nhà hiện tại của tòa.
- Chỉ cờ `is_staff`/`is_superuser` không thay vai trò nghiệp vụ ADMIN. Không lấy vai trò, chủ nhà hoặc kết quả quyền từ query/POST.
- `/ho-so/<id>/` là trang xem chỉ đọc, cho tài khoản đã đăng nhập xem thông tin theo bảng trên; không phải quyền sửa hồ sơ. `/ho-so/khach-thue/` là danh sách tên và liên kết cho ADMIN/CHU_NHA/QUAN_LY. Không có căn cước trong danh sách.
- `profile_for_display()` trả dictionary đã phân quyền; template trang xem không nhận model hồ sơ thô. Response có `Cache-Control: private, no-store`; không gửi số đầy đủ trong hidden input, data attribute hay JavaScript cho người không đủ quyền.
- `/ho-so/` vẫn là trang sửa của khách thuê. Số đã lưu hiển thị dạng che; ô thay số dùng PasswordInput, không prefill số cũ hoặc echo số vừa POST khi có lỗi. Để trống giữ số cũ; gửi chuỗi có dấu * không phải cập nhật hợp lệ.
- Ảnh vẫn hoạt động cho chủ hồ sơ; các URL theo ID cũng kiểm tra quyền mỗi request. ADMIN/chủ nhà đúng phòng xem được ảnh; chủ nhà khác/quản lý/khách khác nhận 403. Ảnh gốc của chính khách thuê vẫn có thể chứa căn cước như trước; task chỉ che trường số, không OCR/che nội dung ảnh.

## Demo phân quyền

1. Khách thuê khai báo hồ sơ, chọn **Xem hồ sơ đã lưu**, ghi lại URL `/ho-so/<id>/`.
2. Dùng quản trị có vai trò ADMIN và quyền Django Admin: tại `/admin/` tạo tòa với đúng chủ nhà, phòng thuộc tòa, hợp đồng với khách đứng tên là hồ sơ trên, trạng thái **Đang hiệu lực**; tạo kỳ thuê chứa hôm nay. Chỉ quản trị có quyền Django được sửa các quan hệ này.
3. Đăng nhập lần lượt khách thuê, chủ nhà đúng tòa, chủ nhà khác, quản lý và ADMIN, mở cùng URL. Đối chiếu bảng trên; chủ nhà/ADMIN/quản lý cũng có mục **Hồ sơ khách thuê** trong menu.
4. Lặp lại với căn cước 9 và 12 số. Kiểm tra mã nguồn HTML của tài khoản bị che không chứa số đầy đủ; thử truy cập URL ảnh của hồ sơ khác.
5. Đổi hợp đồng sang **Đã kết thúc**, tải lại trang của chủ nhà: số chuyển về dạng che, ảnh không còn được cấp quyền. ADMIN vẫn xem đầy đủ.
6. Khách thuê chỉnh nghề nghiệp hoặc thay ảnh, để trống ô căn cước; số cũ được bảo toàn. Nhập số mới hợp lệ để thay, mở lại chỉ thấy 4 số cuối.
