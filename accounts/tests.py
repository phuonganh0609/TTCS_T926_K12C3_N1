import json
import time
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import identify_hasher
from accounts.models import VaiTro, PhienDangNhap, ThuHoiAccessToken
from accounts.tokens import (
    create_tokens_for_user,
    verify_access_token,
    refresh_access_token,
    revoke_tokens,
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
)
import jwt
from django.conf import settings

TaiKhoan = get_user_model()


class DangKyTaiKhoanTests(TestCase):
    """
    Bộ kiểm thử S1-01 (14 ca) — Đăng ký tài khoản Khách thuê.
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
        self.assertRedirects(response, self.trang_chu_url)
        self.assertEqual(TaiKhoan.objects.count(), 1)
        user = TaiKhoan.objects.get(email='khachthue1@example.com')
        self.assertEqual(user.vai_tro, VaiTro.KHACH_THUE)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)
        self.assertContains(response, 'Đăng ký thành công.')
        self.assertContains(response, 'Nguyễn Văn Thuê')
        self.assertContains(response, 'Khách thuê')

    # Ca 2: Điện thoại thiếu/thừa số, không bắt đầu bằng 0, có ký tự sai đều bị từ chối
    def test_02_kiem_tra_dinh_dang_so_dien_thoai(self):
        invalid_phones = [
            '090123456', '09012345678', '1901234567', '090123456a', '0901 34567', '0901-34567',
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
            self.assertContains(response, 'Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0.', msg_prefix=f"Phone {phone}")
            self.assertEqual(TaiKhoan.objects.count(), 0)

    # Ca 3: Mật khẩu dưới 8 ký tự, thiếu chữ, thiếu số đều bị từ chối
    def test_03_kiem_tra_dinh_dang_mat_khau(self):
        invalid_passwords = ['Short1', '12345678', 'MatKhauABC', 'a1b2c3', '']
        for pwd in invalid_passwords:
            data = {
                'ho_ten': 'Người Dùng Test',
                'so_dien_thoai': '0901234567',
                'email': 'test_pwd@example.com',
                'mat_khau': pwd,
            }
            response = self.client.post(self.dang_ky_url, data)
            self.assertEqual(response.status_code, 200, f"Password '{pwd}' should fail validation")
            self.assertContains(response, 'Mật khẩu phải có ít nhất 8 ký tự, gồm ít nhất một chữ cái và một chữ số.')
            self.assertEqual(TaiKhoan.objects.count(), 0)

    # Ca 4: Mật khẩu trong DB không phải rõ; check_password thành công; hasher đúng BCrypt
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
        self.assertNotEqual(user.password, raw_pwd)
        self.assertNotIn(raw_pwd, user.password)
        hasher = identify_hasher(user.password)
        self.assertEqual(hasher.algorithm, 'bcrypt_sha256')
        self.assertTrue(user.check_password(raw_pwd))
        self.assertFalse(user.check_password('SaiMatKhau123'))
        with connection.cursor() as cursor:
            cursor.execute("SELECT mat_khau FROM tai_khoan WHERE email='secure@example.com'")
            row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertTrue(row[0].startswith('bcrypt_sha256$'))
        self.assertNotIn(raw_pwd, row[0])

    # Ca 5: Trùng điện thoại báo đúng trường, số lượng user không tăng
    def test_05_trung_so_dien_thoai_bao_dung_truong(self):
        TaiKhoan.objects.create_user(email='existing@example.com', so_dien_thoai='0909090909', ho_ten='Người A', password='Password123')
        data = {'ho_ten': 'Người B', 'so_dien_thoai': '0909090909', 'email': 'new@example.com', 'mat_khau': 'Password123'}
        response = self.client.post(self.dang_ky_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Số điện thoại này đã được sử dụng.')
        self.assertNotContains(response, 'Email này đã được sử dụng.')
        self.assertEqual(TaiKhoan.objects.count(), 1)

    # Ca 6: Trùng email báo đúng trường, số lượng user không tăng
    def test_06_trung_email_bao_dung_truong(self):
        TaiKhoan.objects.create_user(email='existing@example.com', so_dien_thoai='0911111111', ho_ten='Người A', password='Password123')
        data = {'ho_ten': 'Người B', 'so_dien_thoai': '0922222222', 'email': 'existing@example.com', 'mat_khau': 'Password123'}
        response = self.client.post(self.dang_ky_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email này đã được sử dụng.')
        self.assertNotContains(response, 'Số điện thoại này đã được sử dụng.')
        self.assertEqual(TaiKhoan.objects.count(), 1)

    # Ca 7: Trùng cả hai hiện đủ hai lỗi
    def test_07_trung_ca_hai_hien_du_hai_loi(self):
        TaiKhoan.objects.create_user(email='both@example.com', so_dien_thoai='0933333333', ho_ten='Người Gốc', password='Password123')
        data = {'ho_ten': 'Người Mới', 'so_dien_thoai': '0933333333', 'email': 'both@example.com', 'mat_khau': 'Password123'}
        response = self.client.post(self.dang_ky_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Số điện thoại này đã được sử dụng.')
        self.assertContains(response, 'Email này đã được sử dụng.')
        self.assertEqual(TaiKhoan.objects.count(), 1)

    # Ca 8: Email khác hoa/thường bị coi là trùng
    def test_08_email_khac_hoa_thuong_bi_coi_la_trung(self):
        TaiKhoan.objects.create_user(email='testcase@example.com', so_dien_thoai='0944444444', ho_ten='Người A', password='Password123')
        data = {'ho_ten': 'Người B', 'so_dien_thoai': '0955555555', 'email': 'TestCase@EXAMPLE.Com', 'mat_khau': 'Password123'}
        response = self.client.post(self.dang_ky_url, data)
        self.assertContains(response, 'Email này đã được sử dụng.')
        self.assertEqual(TaiKhoan.objects.count(), 1)

    # Ca 9: Gửi thêm vai trò không nâng quyền được
    def test_09_gui_them_vai_tro_khong_the_nang_quyen(self):
        data = {'ho_ten': 'Hacker', 'so_dien_thoai': '0966666666', 'email': 'hacker@example.com', 'mat_khau': 'Password123', 'vai_tro': 'ADMIN', 'is_staff': True, 'is_superuser': True}
        response = self.client.post(self.dang_ky_url, data, follow=True)
        self.assertRedirects(response, self.trang_chu_url)
        user = TaiKhoan.objects.get(email='hacker@example.com')
        self.assertEqual(user.vai_tro, VaiTro.KHACH_THUE)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    # Ca 10: Bỏ qua JavaScript vẫn bị backend kiểm tra
    def test_10_bo_qua_javascript_van_bi_backend_kiem_tra(self):
        response = self.client.post(self.dang_ky_url, {'ho_ten': '', 'so_dien_thoai': 'invalid', 'email': 'invalid', 'mat_khau': '123'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vui lòng nhập họ và tên.')
        self.assertContains(response, 'Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0.')
        self.assertContains(response, 'Địa chỉ email không đúng định dạng.')
        self.assertContains(response, 'Mật khẩu phải có ít nhất 8 ký tự, gồm ít nhất một chữ cái và một chữ số.')
        self.assertEqual(TaiKhoan.objects.count(), 0)

    # Ca 11: Đăng ký thất bại không tạo dữ liệu dở dang/phiên mới
    def test_11_dang_ky_that_bai_khong_tao_du_lieu_do_dang(self):
        data = {'ho_ten': 'Khách Lỗi', 'so_dien_thoai': '0900000000', 'email': 'invalid-email', 'mat_khau': 'MatKhau123'}
        response = self.client.post(self.dang_ky_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TaiKhoan.objects.count(), 0)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, 'value="Khách Lỗi"')
        self.assertNotContains(response, 'value="MatKhau123"')

    # Ca 12: Dữ liệu hoàn toàn mới tiếp tục hoạt động
    def test_12_du_lieu_hoan_toan_moi_tiep_tuc_hoat_dong(self):
        TaiKhoan.objects.create_user(email='user1@example.com', so_dien_thoai='0977111222', ho_ten='User 1', password='Password123')
        res_trung = self.client.post(self.dang_ky_url, {'ho_ten': 'User Trùng', 'so_dien_thoai': '0977111222', 'email': 'user1@example.com', 'mat_khau': 'Password123'})
        self.assertEqual(res_trung.status_code, 200)
        self.assertEqual(TaiKhoan.objects.count(), 1)
        res_moi = self.client.post(self.dang_ky_url, {'ho_ten': 'User 2 Mới', 'so_dien_thoai': '0977333444', 'email': 'user2@example.com', 'mat_khau': 'Password123'}, follow=True)
        self.assertRedirects(res_moi, self.trang_chu_url)
        self.assertEqual(TaiKhoan.objects.count(), 2)

    # Ca 13: Kiểm tra CSRF và trang đích yêu cầu đăng nhập
    def test_13_csrf_va_trang_dich_yeu_cau_dang_nhap(self):
        response = self.client.get(self.trang_chu_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dang-nhap/', response.url)
        self.assertIn('next=', response.url)
        get_res = self.client.get(self.dang_ky_url)
        self.assertContains(get_res, 'csrfmiddlewaretoken')
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_response = csrf_client.post(self.dang_ky_url, {'ho_ten': 'Test', 'so_dien_thoai': '0988776655', 'email': 'csrf@example.com', 'mat_khau': 'Password123'})
        self.assertEqual(csrf_response.status_code, 403)

    # Ca 14: Kiểm tra giao diện responsive
    def test_14_kiem_tra_giao_dien_va_cau_truc_responsive(self):
        response = self.client.get(self.dang_ky_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        self.assertContains(response, 'bootstrap.min.css')
        self.assertContains(response, 'name="ho_ten"')
        self.assertContains(response, 'name="so_dien_thoai"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="mat_khau"')
        self.assertContains(response, 'blur')
        self.assertContains(response, 'submit')


class DangKyApiTests(TestCase):
    """Kiểm thử API đăng ký tài khoản khách thuê."""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('api_register')

    def test_dang_ky_api_hop_le_tra_token_va_luu_mat_khau_bam(self):
        data = {
            'ho_ten': 'Khách thuê API',
            'so_dien_thoai': '0907654321',
            'email': 'api@example.com',
            'mat_khau': 'ApiPass123',
        }
        response = self.client.post(self.register_url, json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertIn('access_token', body['tokens'])
        self.assertIn('refresh_token', body['tokens'])
        self.assertEqual(body['user']['vai_tro'], VaiTro.KHACH_THUE)

        user = TaiKhoan.objects.get(email=data['email'])
        self.assertNotEqual(user.password, data['mat_khau'])
        self.assertTrue(user.check_password(data['mat_khau']))
        self.assertEqual(PhienDangNhap.objects.filter(tai_khoan=user).count(), 1)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_dang_ky_api_tra_loi_validation_theo_tung_truong(self):
        data = {
            'ho_ten': 'Dữ liệu lỗi',
            'so_dien_thoai': '123456789',
            'email': 'invalid-email',
            'mat_khau': '12345678',
        }
        response = self.client.post(self.register_url, json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        field_errors = response.json()['field_errors']
        self.assertIn('so_dien_thoai', field_errors)
        self.assertIn('email', field_errors)
        self.assertIn('mat_khau', field_errors)
        self.assertEqual(TaiKhoan.objects.count(), 0)

    def test_dang_ky_api_trung_email_va_so_dien_thoai_tra_400(self):
        TaiKhoan.objects.create_user(
            email='existing@example.com',
            so_dien_thoai='0911111111',
            ho_ten='Tài khoản cũ',
            password='Password123',
        )
        data = {
            'ho_ten': 'Tài khoản mới',
            'so_dien_thoai': '0911111111',
            'email': 'existing@example.com',
            'mat_khau': 'Password123',
        }
        response = self.client.post(self.register_url, json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        field_errors = response.json()['field_errors']
        self.assertIn('so_dien_thoai', field_errors)
        self.assertIn('email', field_errors)
        self.assertEqual(TaiKhoan.objects.count(), 1)


class DangNhapTokenTests(TestCase):
    """
    Bộ kiểm thử S1-02 Task 1 — Đăng nhập và duy trì phiên làm việc (Token JWT).
    """

    def setUp(self):
        self.client = Client()
        self.api_login_url = reverse('api_login')
        self.api_refresh_url = reverse('api_refresh')
        self.api_logout_url = reverse('api_logout')
        self.api_me_url = reverse('api_me')
        self.dang_nhap_url = reverse('dang_nhap')
        self.user = TaiKhoan.objects.create_user(
            email='tenant@example.com',
            so_dien_thoai='0901111111',
            ho_ten='Khách Thuê Test',
            password='TestPass123',
        )

    def test_01_dang_nhap_dung_tra_ve_access_token_va_refresh_token(self):
        """Đăng nhập đúng trả về access token (30 phút) và refresh token (7 ngày)."""
        data = json.dumps({'email_or_phone': 'tenant@example.com', 'mat_khau': 'TestPass123'})
        response = self.client.post(self.api_login_url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertTrue(body['success'])
        tokens = body['tokens']

        # Có đủ access_token và refresh_token
        self.assertIn('access_token', tokens)
        self.assertIn('refresh_token', tokens)
        self.assertEqual(tokens['expires_in'], 1800)          # 30 phút
        self.assertEqual(tokens['refresh_expires_in'], 604800) # 7 ngày

        # Kiểm tra nội dung access token
        at_payload = jwt.decode(tokens['access_token'], settings.SECRET_KEY, algorithms=['HS256'])
        self.assertEqual(at_payload['token_type'], 'access')
        self.assertEqual(at_payload['vai_tro'], 'KHACH_THUE')

        # Kiểm tra nội dung refresh token
        rt_payload = jwt.decode(tokens['refresh_token'], settings.SECRET_KEY, algorithms=['HS256'])
        self.assertEqual(rt_payload['token_type'], 'refresh')

        # Phiên đăng nhập được lưu vào CSDL
        self.assertEqual(PhienDangNhap.objects.filter(tai_khoan=self.user).count(), 1)

    def test_02_dang_nhap_bang_so_dien_thoai(self):
        """Đăng nhập bằng số điện thoại cũng thành công."""
        data = json.dumps({'email_or_phone': '0901111111', 'mat_khau': 'TestPass123'})
        response = self.client.post(self.api_login_url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_03_access_token_xac_thuc_api_me(self):
        """Access token hợp lệ cho phép truy cập API /api/auth/me/."""
        tokens = create_tokens_for_user(self.user)
        response = self.client.get(
            self.api_me_url,
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], 'tenant@example.com')

    def test_04_access_token_het_han_tra_ve_401(self):
        """Access token hết hạn trả về mã 401."""
        now = timezone.now()
        import uuid
        expired_payload = {
            'user_id': self.user.id,
            'email': self.user.email,
            'jti': str(uuid.uuid4()),
            'token_type': 'access',
            'iat': int((now - timedelta(hours=2)).timestamp()),
            'exp': int((now - timedelta(hours=1)).timestamp()),  # đã hết hạn
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')
        response = self.client.get(self.api_me_url, HTTP_AUTHORIZATION=f"Bearer {expired_token}")
        self.assertEqual(response.status_code, 401)

    def test_05_refresh_token_con_han_lay_access_token_moi(self):
        """Refresh token còn hạn đổi được access token mới (30 phút)."""
        tokens = create_tokens_for_user(self.user)
        data = json.dumps({'refresh_token': tokens['refresh_token']})
        response = self.client.post(self.api_refresh_url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('access_token', body)
        self.assertEqual(body['expires_in'], 1800)

        # Access token mới xác thực được
        new_at = body['access_token']
        me_response = self.client.get(self.api_me_url, HTTP_AUTHORIZATION=f"Bearer {new_at}")
        self.assertEqual(me_response.status_code, 200)

    def test_06_refresh_token_da_bi_thu_hoi_tra_ve_loi(self):
        """Refresh token đã bị vô hiệu hóa (sau đăng xuất) không đổi được access token mới."""
        tokens = create_tokens_for_user(self.user)
        # Thu hồi phiên đăng nhập
        rt_payload = jwt.decode(tokens['refresh_token'], settings.SECRET_KEY, algorithms=['HS256'])
        PhienDangNhap.objects.filter(token_id=rt_payload['jti']).update(da_thu_hoi=True)

        data = json.dumps({'refresh_token': tokens['refresh_token']})
        response = self.client.post(self.api_refresh_url, data, content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_07_sai_thong_tin_dang_nhap_hien_thong_bao_chung(self):
        """Sai mật khẩu hoặc sai email/số điện thoại đều hiện cùng một thông báo lỗi chung."""
        # Sai mật khẩu
        data = json.dumps({'email_or_phone': 'tenant@example.com', 'mat_khau': 'SaiMatKhau999'})
        resp1 = self.client.post(self.api_login_url, data, content_type='application/json')
        self.assertEqual(resp1.status_code, 400)
        self.assertIn('Thông tin đăng nhập không chính xác.', resp1.json()['error'])

        # Sai email/số điện thoại
        data2 = json.dumps({'email_or_phone': 'khongton@example.com', 'mat_khau': 'TestPass123'})
        resp2 = self.client.post(self.api_login_url, data2, content_type='application/json')
        self.assertEqual(resp2.status_code, 400)
        self.assertIn('Thông tin đăng nhập không chính xác.', resp2.json()['error'])

        # Hai thông báo lỗi phải giống nhau
        self.assertEqual(resp1.json()['error'], resp2.json()['error'])

    def test_08_dang_nhap_web_hien_thong_bao_sai(self):
        """Giao diện web hiển thị thông báo lỗi khi sai thông tin đăng nhập."""
        response = self.client.post(self.dang_nhap_url, {'email_or_phone': 'tenant@example.com', 'mat_khau': 'SaiMatKhau'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thông tin đăng nhập không chính xác.')

    def test_09_verify_access_token_utility(self):
        """Hàm verify_access_token trả về user hợp lệ hoặc None."""
        tokens = create_tokens_for_user(self.user)
        result = verify_access_token(tokens['access_token'])
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.user.id)

        # Token giả trả về None
        self.assertIsNone(verify_access_token('invalid.token.string'))
        self.assertIsNone(verify_access_token(None))


class KhoaTaiKhoanTests(TestCase):
    """
    Bộ kiểm thử S1-02 Task 2 — Tạm khóa tài khoản khi sai mật khẩu liên tiếp 5 lần.
    """

    def setUp(self):
        self.client = Client()
        self.api_login_url = reverse('api_login')
        self.dang_nhap_url = reverse('dang_nhap')
        self.user = TaiKhoan.objects.create_user(
            email='locktest@example.com',
            so_dien_thoai='0902222222',
            ho_ten='Lock Test User',
            password='CorrectPass123',
        )

    def _login_fail(self, n=1):
        """Thực hiện n lần đăng nhập sai mật khẩu qua API."""
        for _ in range(n):
            self.client.post(
                self.api_login_url,
                json.dumps({'email_or_phone': 'locktest@example.com', 'mat_khau': 'SaiMat999'}),
                content_type='application/json'
            )

    def test_01_sai_mat_khau_5_lan_bi_khoa(self):
        """Sai mật khẩu 5 lần trong 15 phút thì bị khóa 15 phút."""
        self._login_fail(4)
        # Lần thứ 4 chưa bị khóa
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_locked())

        # Lần thứ 5 -> bị khóa
        response = self.client.post(
            self.api_login_url,
            json.dumps({'email_or_phone': 'locktest@example.com', 'mat_khau': 'SaiMat999'}),
            content_type='application/json'
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
        self.assertGreater(self.user.get_remaining_lock_seconds(), 0)
        self.assertLessEqual(self.user.get_remaining_lock_seconds(), 900)
        self.assertEqual(response.status_code, 423)
        self.assertTrue(response.json()['is_locked'])

    def test_02_nhap_dung_mat_khau_luc_bi_khoa_van_bi_tu_choi(self):
        """Nhập đúng mật khẩu trong thời gian bị khóa vẫn bị từ chối."""
        self._login_fail(5)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())

        # Nhập đúng mật khẩu nhưng đang bị khóa
        response = self.client.post(
            self.api_login_url,
            json.dumps({'email_or_phone': 'locktest@example.com', 'mat_khau': 'CorrectPass123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 423)
        self.assertTrue(response.json()['is_locked'])

    def test_03_hien_thi_thoi_gian_con_lai_khi_bi_khoa(self):
        """Giao diện web hiển thị thời gian còn lại khi bị khóa."""
        # Khóa tài khoản trực tiếp
        self.user.khoa_den = timezone.now() + timedelta(minutes=15)
        self.user.so_lan_sai = 5
        self.user.save()

        response = self.client.post(
            self.dang_nhap_url,
            {'email_or_phone': 'locktest@example.com', 'mat_khau': 'SaiMat999'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'lockoutAlert')
        self.assertContains(response, 'countdownDisplay')

    def test_04_het_thoi_gian_khoa_dang_nhap_lai_duoc(self):
        """Sau khi hết thời gian khóa, đăng nhập lại được bình thường."""
        # Giả lập khóa đã hết hạn
        self.user.khoa_den = timezone.now() - timedelta(seconds=1)
        self.user.so_lan_sai = 5
        self.user.save()

        response = self.client.post(
            self.api_login_url,
            json.dumps({'email_or_phone': 'locktest@example.com', 'mat_khau': 'CorrectPass123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        # Số lần sai được reset
        self.user.refresh_from_db()
        self.assertEqual(self.user.so_lan_sai, 0)
        self.assertIsNone(self.user.khoa_den)

    def test_05_dang_nhap_thanh_cong_reset_so_lan_sai(self):
        """Đăng nhập thành công đặt lại số lần sai trước đó về 0."""
        self._login_fail(3)
        self.user.refresh_from_db()
        self.assertEqual(self.user.so_lan_sai, 3)

        response = self.client.post(
            self.api_login_url,
            json.dumps({'email_or_phone': 'locktest@example.com', 'mat_khau': 'CorrectPass123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.so_lan_sai, 0)
        self.assertIsNone(self.user.khoa_den)


class DangXuatTests(TestCase):
    """
    Bộ kiểm thử S1-02 Task 3 — Đăng xuất và vô hiệu hóa phiên làm việc.
    """

    def setUp(self):
        self.client = Client()
        self.api_login_url = reverse('api_login')
        self.api_logout_url = reverse('api_logout')
        self.api_me_url = reverse('api_me')
        self.api_refresh_url = reverse('api_refresh')
        self.dang_nhap_url = reverse('dang_nhap')
        self.user = TaiKhoan.objects.create_user(
            email='logout@example.com',
            so_dien_thoai='0903333333',
            ho_ten='Logout Test User',
            password='LogoutPass123',
        )

    def _get_tokens(self):
        """Lấy bộ token bằng cách đăng nhập qua API."""
        resp = self.client.post(
            self.api_login_url,
            json.dumps({'email_or_phone': 'logout@example.com', 'mat_khau': 'LogoutPass123'}),
            content_type='application/json'
        )
        return resp.json()['tokens']

    def test_01_dang_xuat_chuyen_ve_trang_dang_nhap(self):
        """Bấm đăng xuất chuyển về màn hình đăng nhập."""
        self.client.login(email='logout@example.com', password='LogoutPass123')
        self.client.cookies['refresh_token'] = 'fake'
        response = self.client.get(reverse('dang_xuat'), follow=True)
        self.assertRedirects(response, self.dang_nhap_url)

    def test_02_refresh_token_cu_sau_dang_xuat_tra_ve_loi(self):
        """Gọi lại API đổi token bằng refresh token cũ sau đăng xuất trả về lỗi."""
        tokens = self._get_tokens()

        # Đăng xuất qua API
        self.client.post(
            self.api_logout_url,
            json.dumps({'refresh_token': tokens['refresh_token']}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}"
        )

        # Thử refresh lại bằng token cũ -> 401
        resp = self.client.post(
            self.api_refresh_url,
            json.dumps({'refresh_token': tokens['refresh_token']}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 401)

    def test_03_access_token_cu_sau_dang_xuat_tra_ve_401(self):
        """Gọi API /me bằng access token cũ sau đăng xuất trả về mã 401."""
        tokens = self._get_tokens()

        # Đăng xuất
        self.client.post(
            self.api_logout_url,
            json.dumps({'refresh_token': tokens['refresh_token']}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}"
        )

        # Gọi lại bằng access token cũ -> 401
        me_resp = self.client.get(self.api_me_url, HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
        self.assertEqual(me_resp.status_code, 401)

    def test_04_dang_nhap_lai_binh_thuong_sau_dang_xuat(self):
        """Sau khi đăng xuất, đăng nhập lại bình thường với token mới hoàn toàn."""
        tokens_old = self._get_tokens()

        # Đăng xuất
        self.client.post(
            self.api_logout_url,
            json.dumps({'refresh_token': tokens_old['refresh_token']}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {tokens_old['access_token']}"
        )

        # Đăng nhập lại
        resp = self.client.post(
            self.api_login_url,
            json.dumps({'email_or_phone': 'logout@example.com', 'mat_khau': 'LogoutPass123'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        tokens_new = resp.json()['tokens']
        self.assertNotEqual(tokens_new['access_token'], tokens_old['access_token'])
        self.assertNotEqual(tokens_new['refresh_token'], tokens_old['refresh_token'])

        # Token mới dùng được
        me_resp = self.client.get(self.api_me_url, HTTP_AUTHORIZATION=f"Bearer {tokens_new['access_token']}")
        self.assertEqual(me_resp.status_code, 200)

    def test_05_revoke_tokens_utility(self):
        """Hàm revoke_tokens vô hiệu hóa đúng cả access token lẫn refresh token."""
        tokens = create_tokens_for_user(self.user)
        revoke_tokens(refresh_token_str=tokens['refresh_token'], access_token_str=tokens['access_token'], user=self.user)

        # Access token bị đưa vào blacklist
        at_payload = jwt.decode(tokens['access_token'], settings.SECRET_KEY, algorithms=['HS256'])
        self.assertTrue(ThuHoiAccessToken.objects.filter(jti=at_payload['jti']).exists())

        # Refresh token bị thu hồi trong CSDL
        rt_payload = jwt.decode(tokens['refresh_token'], settings.SECRET_KEY, algorithms=['HS256'])
        phien = PhienDangNhap.objects.get(token_id=rt_payload['jti'])
        self.assertTrue(phien.da_thu_hoi)

        # verify_access_token trả về None sau khi thu hồi
        self.assertIsNone(verify_access_token(tokens['access_token']))
