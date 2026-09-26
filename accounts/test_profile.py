from datetime import date

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .models import KhachThue, TaiKhoan, VaiTro


class HoSoKhachThueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = TaiKhoan.objects.create_user(
            email='profile@example.com', so_dien_thoai='0900000001',
            ho_ten='Nguyễn An', password='Profile123',
        )
        cls.other = TaiKhoan.objects.create_user(
            email='other@example.com', so_dien_thoai='0900000002',
            ho_ten='Trần Bình', password='Profile123',
        )

    def setUp(self):
        self.url = reverse('ho_so')
        self.client.force_login(self.user)
        self.data = {
            'ho_ten': 'Nguyễn Văn An', 'ngay_sinh': '2000-02-29',
            'so_giay_to': '012345678', 'que_quan': 'Hà Nội',
            'nghe_nghiep': 'Kỹ sư',
        }

    def test_get_unsaved_profile_does_not_create_record(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['ho_ten'], self.user.ho_ten)
        self.assertFalse(KhachThue.objects.exists())
        self.assertContains(response, 'Hồ sơ cá nhân')
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_save_nine_digits_and_reopen_all_fields(self):
        response = self.client.post(self.url, self.data, follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(response, 'Đã lưu hồ sơ cá nhân thành công.')
        saved = KhachThue.objects.get(tai_khoan=self.user)
        self.assertEqual(saved.ngay_sinh, date(2000, 2, 29))
        for field in ['ho_ten', 'so_giay_to', 'que_quan', 'nghe_nghiep']:
            self.assertEqual(getattr(saved, field), self.data[field])
        reopened = self.client.get(self.url)
        for key, value in self.data.items():
            if key != 'so_giay_to':
                self.assertContains(reopened, value)
        self.assertContains(reopened, '*****5678')
        self.assertNotContains(reopened, self.data['so_giay_to'])

    def test_save_twelve_digits(self):
        self.data['so_giay_to'] = '001234567890'
        self.assertRedirects(self.client.post(self.url, self.data), self.url)
        self.assertEqual(KhachThue.objects.get().so_giay_to, '001234567890')

    def test_invalid_identity_reports_field_error_without_saving(self):
        invalid = ['', '12345678', '1234567890', '12345678901', '1234567890123',
                   '12345678a', '1234-6789', '1234 6789', '１２３４５６７８９',
                   ' 012345678', '012345678\n']
        for identity in invalid:
            with self.subTest(identity=identity):
                response = self.client.post(self.url, {**self.data, 'so_giay_to': identity})
                self.assertEqual(response.status_code, 200)
                self.assertIn('so_giay_to', response.context['form'].errors)
                self.assertContains(response, 'id_so_giay_to_errors')
                self.assertContains(response, 'aria-invalid="true"')
                self.assertContains(response, self.data['que_quan'])
                self.assertFalse(KhachThue.objects.exists())

    def test_edit_updates_same_profile_and_reopens(self):
        self.client.post(self.url, self.data)
        profile_id = KhachThue.objects.get().pk
        edited = {
            'ho_ten': 'Nguyễn An Mới', 'ngay_sinh': '1999-12-31',
            'so_giay_to': '009876543210', 'que_quan': 'Đà Nẵng',
            'nghe_nghiep': 'Giáo viên',
        }
        self.assertRedirects(self.client.post(self.url, edited), self.url)
        self.assertEqual(KhachThue.objects.count(), 1)
        saved = KhachThue.objects.get(pk=profile_id)
        self.assertEqual(saved.ngay_sinh, date(1999, 12, 31))
        for field in ['ho_ten', 'so_giay_to', 'que_quan', 'nghe_nghiep']:
            self.assertEqual(getattr(saved, field), edited[field])
        reopened = self.client.get(self.url)
        for key, value in edited.items():
            if key != 'so_giay_to':
                self.assertContains(reopened, value)
        self.assertContains(reopened, '********3210')
        self.assertNotContains(reopened, edited['so_giay_to'])

    def test_invalid_edit_preserves_saved_profile(self):
        self.client.post(self.url, self.data)
        response = self.client.post(self.url, {**self.data, 'so_giay_to': 'abc', 'ho_ten': 'Tên mới'})
        self.assertEqual(response.status_code, 200)
        saved = KhachThue.objects.get()
        self.assertEqual(saved.so_giay_to, self.data['so_giay_to'])
        self.assertEqual(saved.ho_ten, self.data['ho_ten'])

    def test_required_fields_and_invalid_date(self):
        for field in self.data:
            with self.subTest(field=field):
                response = self.client.post(self.url, {**self.data, field: ''})
                self.assertIn(field, response.context['form'].errors)
        response = self.client.post(self.url, {**self.data, 'ngay_sinh': '2001-02-29'})
        self.assertIn('ngay_sinh', response.context['form'].errors)
        self.assertFalse(KhachThue.objects.exists())

    def test_other_profile_cannot_be_read_or_modified_by_submitted_ids(self):
        other_profile = KhachThue.objects.create(tai_khoan=self.other, **self.data)
        response = self.client.get(self.url, {'id': other_profile.pk, 'tai_khoan': self.other.pk})
        self.assertIsNone(response.context['form'].instance.pk)
        self.client.post(self.url, {
            **self.data, 'ho_ten': 'Hồ sơ của tôi',
            'id': other_profile.pk, 'tai_khoan': self.other.pk, 'tai_khoan_id': self.other.pk,
        })
        other_profile.refresh_from_db()
        self.assertEqual(other_profile.ho_ten, self.data['ho_ten'])
        self.assertEqual(KhachThue.objects.get(tai_khoan=self.user).ho_ten, 'Hồ sơ của tôi')

    def test_requires_login(self):
        self.client.logout()
        for method in [self.client.get, self.client.post]:
            response = method(self.url)
            self.assertRedirects(response, reverse('dang_nhap') + '?next=' + self.url)
        self.assertFalse(KhachThue.objects.exists())

    def test_other_roles_cannot_access_tenant_profile(self):
        for role in [VaiTro.CHU_NHA, VaiTro.QUAN_LY, VaiTro.ADMIN]:
            with self.subTest(role=role):
                self.user.vai_tro = role
                self.user.save(update_fields=['vai_tro'])
                self.assertEqual(self.client.get(self.url).status_code, 403)
                self.assertEqual(self.client.post(self.url, self.data).status_code, 403)
        self.assertFalse(KhachThue.objects.exists())

    def test_csrf_required_and_valid_submission_accepted(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url, self.data).status_code, 403)
        client.get(self.url)
        response = client.post(self.url, {
            **self.data, 'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        })
        self.assertRedirects(response, self.url)

    def test_model_validation_rejects_invalid_identity(self):
        profile = KhachThue(tai_khoan=self.user, **{**self.data, 'so_giay_to': '12345678x'})
        with self.assertRaises(ValidationError) as error:
            profile.full_clean()
        self.assertIn('so_giay_to', error.exception.message_dict)
