import re
import sqlite3
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import identify_hasher
from django.conf import settings
from accounts.models import VaiTro

TaiKhoan = get_user_model()


class DangKyTaiKhoanTests(TestCase):
    """
    Bộ kiểm thử bao quát toàn bộ 14 ca kiểm thử được quy định
    tại 03-task-dang-ky.md cho Story S1-01 (Task 1 và Task 2).
    """

    def setUp(self):
        self.client = Client()
        self.dang_ky_url = reverse('dang_ky')
        self.trang_chu_url = reverse('trang_chu')

    # Ca 1: Đăng ký hợp lệ tạo đúng một user, role KHACH_THUE, tự đăng nhập và chuyển đúng trang
    def test_01_dang_ky_hop_le_tao_user_vai_tro_khach_thue_va_tu_dang_nhap(self):
        data = {
            'ho_ten': 'Nguyễn Văn Thuê',
            'so_dien_thoai': '0901234567',
            'email': 'khachthue1@example.com',
            'mat_khau': 'MatKhau123',
        }
        response = self.client.post(self.dang_ky_url, data, follow=True)

        # Chuyển hướng đúng trang đích
        self.assertRedirects(response, self.trang_chu_url)

        # Tạo đúng 1 user
        self.assertEqual(TaiKhoan.objects.count(), 1)
        user = TaiKhoan.objects.get(email='khachthue1@example.com')

        # Role KHACH_THUE, không nâng quyền
        self.assertEqual(user.vai_tro, VaiTro.KHACH_THUE)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

        # Tự động đăng nhập qua session
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        # Hiển thị thông báo thành công và thông tin trên trang đích
        self.assertContains(response, 'Đăng ký thành công.')
        self.assertContains(response, 'Nguyễn Văn Thuê')
        self.assertContains(response, 'Khách thuê')

    # Ca 2: Điện thoại thiếu/thừa số, không bắt đầu bằng 0, có ký tự sai đều bị từ chối
    def test_02_kiem_tra_dinh_dang_so_dien_thoai(self):
        invalid_phones = [
            '090123456',     # 9 số (thiếu)
            '09012345678',   # 11 số (thừa)
            '1901234567',    # không bắt đầu bằng 0
            '090123456a',    # chứa chữ cái
            '0901 34567',    # chứa khoảng trắng ở giữa
            '0901-34567',    # chứa ký tự đặc biệt
        ]
        for phone in invalid_phones:
            data = {
                'ho_ten': 'Người Dùng Test',
                'so_dien_thoai': phone,
                'email': f'test_{phone.replace(" ", "_")}@example.com',
                'mat_khau': 'MatKhau123',
            }
            response = self.client.post(self.dang_ky_url, data)
            self.assertEqual(response.status_code, 200, f"Phone {phone} should fail validation")
            self.assertContains(
                response,
                'Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0.',
                msg_prefix=f"Phone {phone} missing error message"
            )
            self.assertEqual(TaiKhoan.objects.count(), 0)

    # Ca 3: Mật khẩu dưới 8 ký tự, thiếu chữ, thiếu số đều bị từ chối
    def test_03_kiem_tra_dinh_dang_mat_khau(self):
        invalid_passwords = [
            'Short1',        # 6 ký tự (< 8)
            '12345678',      # thiếu chữ
            'MatKhauABC',    # thiếu số
            'a1b2c3',        # 6 ký tự (< 8)
            '',              # rỗng
        ]
        for pwd in invalid_passwords:
            data = {
                'ho_ten': 'Người Dùng Test',
                'so_dien_thoai': '0901234567',
                'email': 'test_pwd@example.com',
                'mat_khau': pwd,
            }
            response = self.client.post(self.dang_ky_url, data)
            self.assertEqual(response.status_code, 200, f"Password {pwd} should fail validation")
            self.assertContains(
                response,
                'Mật khẩu phải có ít nhất 8 ký tự, gồm ít nhất một chữ cái và một chữ số.'
            )
            self.assertEqual(TaiKhoan.objects.count(), 0)

    # Ca 4: Mật khẩu trong DB không phải rõ; check_password thành công; hasher đúng BCrypt đã cấu hình
    def test_04_mat_khau_bam_bcrypt_khong_luu_thuan(self):
        from django.db import connection

        raw_pwd = 'MySecretPassword123'
        data = {
            'ho_ten': 'Trần Văn Bảo Mật',
            'so_dien_thoai': '0911223344',
            'email': 'secure@example.com',
            'mat_khau': raw_pwd,
        }
        self.client.post(self.dang_ky_url, data)
        user = TaiKhoan.objects.get(email='secure@example.com')

        # 1. Không lưu rõ trong thuộc tính password
        self.assertNotEqual(user.password, raw_pwd)
        self.assertNotIn(raw_pwd, user.password)

        # 2. Hasher đúng BCrypt đã cấu hình
        hasher = identify_hasher(user.password)
        self.assertEqual(hasher.algorithm, 'bcrypt_sha256')

        # 3. check_password thành công
        self.assertTrue(user.check_password(raw_pwd))
        self.assertFalse(user.check_password('SaiMatKhau123'))

        # 4. Kiểm tra trực tiếp tại cột CSDL SQLite 'mat_khau' trong test database
        with connection.cursor() as cursor:
            cursor.execute("SELECT mat_khau FROM tai_khoan WHERE email='secure@example.com'")
            row = cursor.fetchone()

        self.assertIsNotNone(row)
        db_mat_khau = row[0]
        self.assertTrue(db_mat_khau.startswith('bcrypt_sha256$'))
        self.assertNotIn(raw_pwd, db_mat_khau)

    # Ca 5: Trùng điện thoại báo đúng trường, số lượng user không tăng
    def test_05_trung_so_dien_thoai_bao_dung_truong(self):
        # Tạo trước 1 tài khoản
        TaiKhoan.objects.create_user(
            email='existing_phone@example.com',
            so_dien_thoai='0909090909',
            ho_ten='Người Dùng A',
            password='Password123'
        )
        self.assertEqual(TaiKhoan.objects.count(), 1)

        # Thử đăng ký với SĐT trùng nhưng email mới
        data = {
            'ho_ten': 'Người Dùng B',
            'so_dien_thoai': '0909090909',
            'email': 'new_email@example.com',
            'mat_khau': 'Password123',
        }
        response = self.client.post(self.dang_ky_url, data)
        self.assertEqual(response.status_code, 200)

        # Báo lỗi tại trường số điện thoại
        self.assertContains(response, 'Số điện thoại này đã được sử dụng.')
        # Không báo lỗi tại email
        self.assertNotContains(response, 'Email này đã được sử dụng.')

        # Số lượng user không tăng
        self.assertEqual(TaiKhoan.objects.count(), 1)

    # Ca 6: Trùng email báo đúng trường, số lượng user không tăng
    def test_06_trung_email_bao_dung_truong(self):
        # Tạo trước 1 tài khoản
        TaiKhoan.objects.create_user(
            email='existing_email@example.com',
            so_dien_thoai='0911111111',
            ho_ten='Người Dùng A',
            password='Password123'
        )
        self.assertEqual(TaiKhoan.objects.count(), 1)

        # Thử đăng ký với Email trùng nhưng SĐT mới
        data = {
            'ho_ten': 'Người Dùng B',
            'so_dien_thoai': '0922222222',
            'email': 'existing_email@example.com',
            'mat_khau': 'Password123',
        }
        response = self.client.post(self.dang_ky_url, data)
        self.assertEqual(response.status_code, 200)

        # Báo lỗi tại trường email
        self.assertContains(response, 'Email này đã được sử dụng.')
        # Không báo lỗi tại SĐT
        self.assertNotContains(response, 'Số điện thoại này đã được sử dụng.')

        # Số lượng user không tăng
        self.assertEqual(TaiKhoan.objects.count(), 1)

    # Ca 7: Trùng cả hai hiện đủ hai lỗi trong một lần gửi
    def test_07_trung_ca_hai_hien_du_hai_loi(self):
        TaiKhoan.objects.create_user(
            email='both_exist@example.com',
            so_dien_thoai='0933333333',
            ho_ten='Người Dùng Gốc',
            password='Password123'
        )
        self.assertEqual(TaiKhoan.objects.count(), 1)

        # Đăng ký trùng cả email và số điện thoại
        data = {
            'ho_ten': 'Người Dùng Mới',
            'so_dien_thoai': '0933333333',
            'email': 'both_exist@example.com',
            'mat_khau': 'Password123',
        }
        response = self.client.post(self.dang_ky_url, data)
        self.assertEqual(response.status_code, 200)

        # Xuất hiện cả 2 thông báo lỗi độc lập
        self.assertContains(response, 'Số điện thoại này đã được sử dụng.')
        self.assertContains(response, 'Email này đã được sử dụng.')

        # Số lượng user không đổi
        self.assertEqual(TaiKhoan.objects.count(), 1)

    # Ca 8: Email khác hoa/thường nhưng cùng giá trị chuẩn hóa bị coi là trùng
    def test_08_email_khac_hoa_thuong_cung_chuan_hoa_bi_coi_la_trung(self):
        TaiKhoan.objects.create_user(
            email='testcase@example.com',
            so_dien_thoai='0944444444',
            ho_ten='Người Dùng Hoa Thường',
            password='Password123'
        )

        data = {
            'ho_ten': 'Người Dùng Khác',
            'so_dien_thoai': '0955555555',
            'email': 'TestCase@EXAMPLE.Com',
            'mat_khau': 'Password123',
        }
        response = self.client.post(self.dang_ky_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email này đã được sử dụng.')
        self.assertEqual(TaiKhoan.objects.count(), 1)

    # Ca 9: Gửi thêm vai trò ADMIN/is_staff/is_superuser không nâng quyền được
    def test_09_gui_them_vai_tro_khong_the_nang_quyen(self):
        data = {
            'ho_ten': 'Hacker Thử Nghiệm',
            'so_dien_thoai': '0966666666',
            'email': 'hacker@example.com',
            'mat_khau': 'Password123',
            'vai_tro': 'ADMIN',
            'is_staff': True,
            'is_superuser': True,
        }
        response = self.client.post(self.dang_ky_url, data, follow=True)
        self.assertRedirects(response, self.trang_chu_url)

        user = TaiKhoan.objects.get(email='hacker@example.com')
        # Tuyệt đối không được nâng quyền
        self.assertEqual(user.vai_tro, VaiTro.KHACH_THUE)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    # Ca 10: Bỏ qua JavaScript vẫn bị backend kiểm tra độc lập
    def test_10_bo_qua_javascript_van_bi_backend_kiem_tra(self):
        # Client HTTP trực tiếp gửi POST không qua browser hay JS
        raw_invalid_data = {
            'ho_ten': '',
            'so_dien_thoai': 'invalid_phone',
            'email': 'invalid_email',
            'mat_khau': '123',
        }
        response = self.client.post(self.dang_ky_url, raw_invalid_data)
        self.assertEqual(response.status_code, 200)

        # Backend bắt toàn bộ lỗi
        self.assertContains(response, 'Vui lòng nhập họ và tên.')
        self.assertContains(response, 'Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0.')
        self.assertContains(response, 'Địa chỉ email không đúng định dạng.')
        self.assertContains(response, 'Mật khẩu phải có ít nhất 8 ký tự, gồm ít nhất một chữ cái và một chữ số.')
        self.assertEqual(TaiKhoan.objects.count(), 0)

    # Ca 11: Đăng ký thất bại không tạo dữ liệu dở dang/phiên mới
    def test_11_dang_ky_that_bai_khong_tao_du_lieu_do_dang_va_khong_co_phien(self):
        data = {
            'ho_ten': 'Khách Lỗi',
            'so_dien_thoai': '0900000000',
            'email': 'invalid-email',
            'mat_khau': 'MatKhau123',
        }
        response = self.client.post(self.dang_ky_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TaiKhoan.objects.count(), 0)

        # Không tạo phiên đăng nhập
        self.assertNotIn('_auth_user_id', self.client.session)

        # Giá trị họ tên, sđt được giữ lại, mật khẩu không điền lại
        self.assertContains(response, 'value="Khách Lỗi"')
        self.assertContains(response, 'value="0900000000"')
        self.assertNotContains(response, 'value="MatKhau123"')

    # Ca 12: Dữ liệu hoàn toàn mới tiếp tục hoạt động sau khi thêm kiểm tra trùng
    def test_12_du_lieu_hoan_toan_moi_tiep_tuc_hoat_dong(self):
        # 1. Tạo user 1
        TaiKhoan.objects.create_user(
            email='user1@example.com',
            so_dien_thoai='0977111222',
            ho_ten='User 1',
            password='Password123'
        )

        # 2. Thử trùng -> từ chối
        data_trung = {
            'ho_ten': 'User Trùng',
            'so_dien_thoai': '0977111222',
            'email': 'user1@example.com',
            'mat_khau': 'Password123',
        }
        res_trung = self.client.post(self.dang_ky_url, data_trung)
        self.assertEqual(res_trung.status_code, 200)
        self.assertEqual(TaiKhoan.objects.count(), 1)

        # 3. Tạo user 2 với dữ liệu mới hoàn toàn -> thành công
        data_moi = {
            'ho_ten': 'User 2 Mới Tinh',
            'so_dien_thoai': '0977333444',
            'email': 'user2@example.com',
            'mat_khau': 'Password123',
        }
        res_moi = self.client.post(self.dang_ky_url, data_moi, follow=True)
        self.assertRedirects(res_moi, self.trang_chu_url)
        self.assertEqual(TaiKhoan.objects.count(), 2)
        self.assertTrue(TaiKhoan.objects.filter(email='user2@example.com').exists())

    # Ca 13: Kiểm tra CSRF và trang đích yêu cầu đăng nhập
    def test_13_csrf_va_trang_dich_yeu_cau_dang_nhap(self):
        # 1. Truy cập trang đích khi chưa đăng nhập -> bị chặn và chuyển hướng
        response = self.client.get(self.trang_chu_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dang-nhap/', response.url)
        self.assertIn('next=', response.url)

        # 2. Kiểm tra trang đăng ký có thẻ CSRF
        get_res = self.client.get(self.dang_ky_url)
        self.assertContains(get_res, 'csrfmiddlewaretoken')

        # 3. POST không có CSRF token khi enforce_csrf_checks=True
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_response = csrf_client.post(self.dang_ky_url, {
            'ho_ten': 'Test CSRF',
            'so_dien_thoai': '0988776655',
            'email': 'csrf@example.com',
            'mat_khau': 'Password123',
        })
        self.assertEqual(csrf_response.status_code, 403)

    # Ca 14: Kiểm tra giao diện trên màn hình điện thoại và máy tính
    def test_14_kiem_tra_giao_dien_va_cau_truc_responsive(self):
        response = self.client.get(self.dang_ky_url)
        self.assertEqual(response.status_code, 200)

        # Thẻ meta viewport cho mobile (từ 360px)
        self.assertContains(response, '<meta name="viewport" content="width=device-width, initial-scale=1.0">')

        # Có thư viện Bootstrap 5
        self.assertContains(response, 'bootstrap.min.css')
        self.assertContains(response, 'bootstrap.bundle.min.js')

        # Có đầy đủ 4 trường input
        self.assertContains(response, 'name="ho_ten"')
        self.assertContains(response, 'name="so_dien_thoai"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="mat_khau"')

        # Có script kiểm tra blur và submit
        self.assertContains(response, 'blur')
        self.assertContains(response, 'submit')
