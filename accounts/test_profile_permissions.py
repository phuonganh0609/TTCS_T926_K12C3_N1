from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import KhachThue, TaiKhoan, VaiTro, ToaNha, PhongTro, HopDong, KyHopDong
from .profile_permissions import mask_identity, can_view_full_identity, profile_for_display


class ProfilePermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        def account(name, role, index, **kwargs):
            return TaiKhoan.objects.create_user(
                email=f'{name}@example.com', so_dien_thoai=f'090000{index:04d}',
                ho_ten=name, vai_tro=role, **kwargs,
            )
        cls.tenant = account('tenant', VaiTro.KHACH_THUE, 1)
        cls.stranger = account('stranger', VaiTro.KHACH_THUE, 2)
        cls.owner = account('owner', VaiTro.CHU_NHA, 3)
        cls.other_owner = account('other-owner', VaiTro.CHU_NHA, 4)
        cls.manager = account('manager', VaiTro.QUAN_LY, 5)
        cls.admin = account('admin', VaiTro.ADMIN, 6, is_staff=True, is_superuser=True)
        cls.data = dict(ho_ten='Khách hồ sơ', ngay_sinh='2000-01-01', so_giay_to='012345678',
                        que_quan='Hà Nội', nghe_nghiep='Kỹ sư')
        cls.profile = KhachThue.objects.create(tai_khoan=cls.tenant, **cls.data)
        cls.building = ToaNha.objects.create(chu_nha=cls.owner, ten_toa_nha='Tòa A')
        cls.room = PhongTro.objects.create(toa_nha=cls.building, ma_phong='101')
        cls.contract = HopDong.objects.create(
            ma_hop_dong='HD-TEST', phong=cls.room, khach_dung_ten=cls.profile,
            trang_thai=HopDong.TrangThai.DANG_HIEU_LUC,
        )
        cls.today = timezone.localdate()
        cls.period = KyHopDong.objects.create(
            hop_dong=cls.contract, ngay_bat_dau=cls.today - timedelta(days=10),
            ngay_ket_thuc=cls.today + timedelta(days=10),
        )

    def setUp(self):
        self.url = reverse('xem_ho_so', args=[self.profile.pk])

    def assert_masked(self, viewer, number):
        self.client.force_login(viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, mask_identity(number))
        self.assertNotContains(response, number)
        self.assertEqual(response.context['profile']['so_giay_to'], mask_identity(number))
        self.assertNotIn(number, str(response.context['profile']))
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        return response

    def test_role_matrix_for_nine_and_twelve_digits(self):
        for number in ['012345678', '001234567890']:
            self.profile.so_giay_to = number
            self.profile.save()
            for viewer in [self.tenant, self.stranger, self.manager, self.other_owner]:
                with self.subTest(number=number, viewer=viewer.ho_ten):
                    self.assert_masked(viewer, number)
            for viewer in [self.owner, self.admin]:
                with self.subTest(number=number, viewer=viewer.ho_ten):
                    self.client.force_login(viewer)
                    response = self.client.get(self.url)
                    self.assertContains(response, number)
                    self.assertEqual(response.context['profile']['so_giay_to'], number)

    def test_mask_format_approved_by_po(self):
        self.assertEqual(mask_identity('123456789'), '*****6789')
        self.assertEqual(mask_identity('123456786789'), '********6789')

    def test_non_active_contracts_never_grant_access(self):
        for status in [HopDong.TrangThai.NHAP, HopDong.TrangThai.CHO_HIEU_LUC,
                       HopDong.TrangThai.DA_KET_THUC, HopDong.TrangThai.DA_HUY]:
            self.contract.trang_thai = status
            self.contract.save()
            self.assert_masked(self.owner, self.profile.so_giay_to)

    def test_expired_future_or_missing_periods_never_grant_access(self):
        for start, end in [(self.today - timedelta(days=30), self.today - timedelta(days=1)),
                           (self.today + timedelta(days=1), self.today + timedelta(days=30))]:
            self.period.ngay_bat_dau, self.period.ngay_ket_thuc = start, end
            self.period.save()
            self.assert_masked(self.owner, self.profile.so_giay_to)
        self.period.delete()
        self.assert_masked(self.owner, self.profile.so_giay_to)

    def test_separate_periods_cannot_combine_to_grant_access(self):
        self.period.ngay_ket_thuc = self.today - timedelta(days=1)
        self.period.save()
        KyHopDong.objects.create(hop_dong=self.contract, so_thu_tu=2,
                                 ngay_bat_dau=self.today + timedelta(days=1),
                                 ngay_ket_thuc=self.today + timedelta(days=30))
        self.assert_masked(self.owner, self.profile.so_giay_to)

    def test_today_boundaries_are_inclusive(self):
        self.period.ngay_bat_dau = self.today
        self.period.ngay_ket_thuc = self.today
        self.period.save()
        self.contract.ngay_tra_phong = self.today
        self.contract.save()
        self.assertTrue(can_view_full_identity(self.owner, self.profile))

    def test_early_checkout_revokes_owner_access(self):
        self.contract.ngay_tra_phong = self.today - timedelta(days=1)
        self.contract.save()
        self.assert_masked(self.owner, self.profile.so_giay_to)
        self.assertTrue(can_view_full_identity(self.admin, self.profile))

    def test_no_contract_and_different_tenant_are_masked(self):
        self.contract.delete()
        self.assert_masked(self.owner, self.profile.so_giay_to)
        other_profile = KhachThue.objects.create(tai_khoan=self.stranger, **self.data)
        other_contract = HopDong.objects.create(ma_hop_dong='HD-OTHER', phong=self.room,
                                               khach_dung_ten=other_profile, trang_thai='DANG_HIEU_LUC')
        KyHopDong.objects.create(hop_dong=other_contract, ngay_bat_dau=self.today,
                                 ngay_ket_thuc=self.today + timedelta(days=1))
        self.assert_masked(self.owner, self.profile.so_giay_to)

    def test_change_owner_recalculates_access_on_next_request(self):
        self.assertTrue(can_view_full_identity(self.owner, self.profile))
        self.building.chu_nha = self.other_owner
        self.building.save()
        self.assert_masked(self.owner, self.profile.so_giay_to)
        self.assertTrue(can_view_full_identity(self.other_owner, self.profile))

    def test_staff_or_superuser_flag_is_not_business_role(self):
        self.manager.is_staff = True
        self.manager.is_superuser = True
        self.manager.save()
        self.assert_masked(self.manager, self.profile.so_giay_to)
        self.assertEqual(self.client.get(reverse('admin:accounts_toanha_add')).status_code, 403)

    def test_inactive_viewer_has_no_full_access(self):
        self.admin.is_active = False
        self.assertFalse(can_view_full_identity(self.admin, self.profile))
        self.owner.is_active = False
        self.assertFalse(can_view_full_identity(self.owner, self.profile))

    def test_query_parameters_cannot_change_identity_permissions(self):
        self.client.force_login(self.stranger)
        response = self.client.get(self.url, {'vai_tro': 'ADMIN', 'user_id': self.admin.pk,
                                               'chu_nha_id': self.owner.pk, 'full': 'true'})
        self.assertNotContains(response, self.profile.so_giay_to)
        self.assertContains(response, '*****5678')

    def test_detail_is_read_only_and_requires_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(self.url, {'so_giay_to': '999999999'}).status_code, 405)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.so_giay_to, self.data['so_giay_to'])

    def test_editor_has_no_raw_number_and_blank_preserves_it(self):
        self.client.force_login(self.tenant)
        edit = reverse('ho_so')
        response = self.client.get(edit)
        self.assertNotContains(response, self.profile.so_giay_to)
        self.assertContains(response, '*****5678')
        self.assertEqual(response.context['form'].initial['so_giay_to'], '')
        self.assertRedirects(self.client.post(edit, {**self.data, 'so_giay_to': '', 'nghe_nghiep': 'Giáo viên'}), edit)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.so_giay_to, self.data['so_giay_to'])
        self.assertEqual(self.profile.nghe_nghiep, 'Giáo viên')

    def test_invalid_post_does_not_echo_old_or_new_number(self):
        self.client.force_login(self.tenant)
        response = self.client.post(reverse('ho_so'), {**self.data, 'so_giay_to': '001234567890', 'ho_ten': ''})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '001234567890')
        self.assertNotContains(response, self.profile.so_giay_to)
        self.assertContains(response, '*****5678')

    def test_masked_value_cannot_overwrite_number(self):
        self.client.force_login(self.tenant)
        response = self.client.post(reverse('ho_so'), {**self.data, 'so_giay_to': '*****5678'})
        self.assertIn('so_giay_to', response.context['form'].errors)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.so_giay_to, self.data['so_giay_to'])

    def test_lists_never_return_full_identity(self):
        for viewer in [self.admin, self.owner, self.other_owner, self.manager]:
            self.client.force_login(viewer)
            response = self.client.get(reverse('danh_sach_ho_so'))
            self.assertContains(response, self.profile.ho_ten)
            self.assertNotContains(response, self.profile.so_giay_to)

    def test_images_not_a_bypass_for_unrelated_viewers(self):
        self.profile.anh_giay_to_truoc = 'giay-to/test.jpg'
        self.profile.save()
        image_url = reverse('anh_ho_so', args=[self.profile.pk, 'truoc'])
        for viewer in [self.stranger, self.manager, self.other_owner]:
            response = self.assert_masked(viewer, self.profile.so_giay_to)
            self.assertNotContains(response, image_url)
            self.assertEqual(self.client.get(image_url).status_code, 403)
        for viewer in [self.tenant, self.owner, self.admin]:
            self.client.force_login(viewer)
            with patch('django.db.models.fields.files.FieldFile.open', return_value=BytesIO(b'image')):
                response = self.client.get(image_url)
                self.assertEqual(response.status_code, 200)
                response.close()
        self.contract.trang_thai = HopDong.TrangThai.DA_KET_THUC
        self.contract.save()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(image_url).status_code, 403)

    def test_display_data_is_plain_safe_dictionary(self):
        data = profile_for_display(self.stranger, self.profile)
        self.assertIsInstance(data, dict)
        self.assertNotIn(self.profile.so_giay_to, str(data))
        self.assertNotIn('tai_khoan', data)
