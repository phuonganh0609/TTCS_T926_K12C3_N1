from io import BytesIO
from pathlib import Path
import shutil
from uuid import uuid4
from unittest.mock import patch

from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import KhachThue, TaiKhoan, VaiTro
from .profile_images import IMAGE_FIELDS, MAX_IMAGE_BYTES


def image_file(fmt='JPEG', size=(800, 500), name=None):
    data = BytesIO()
    Image.new('RGB', size, '#507db5').save(data, format=fmt)
    return SimpleUploadedFile(name or ('photo.png' if fmt == 'PNG' else 'photo.jpg'),
                              data.getvalue(), content_type='application/octet-stream')


class ProfileImageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = TaiKhoan.objects.create_user(
            email='images@example.com', so_dien_thoai='0900060001', ho_ten='Khách ảnh',
        )
        cls.other = TaiKhoan.objects.create_user(
            email='other-images@example.com', so_dien_thoai='0900060002', ho_ten='Khách khác',
        )

    def setUp(self):
        self.media = (settings.BASE_DIR / ('test-profile-images-' + uuid4().hex)).resolve()
        assert self.media.parent == settings.BASE_DIR.resolve()
        self.media.mkdir()
        self.addCleanup(shutil.rmtree, self.media)
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.client.force_login(self.user)
        self.url = reverse('ho_so')
        self.data = dict(ho_ten='Khách ảnh', ngay_sinh='2000-01-01', so_giay_to='001234567890',
                         que_quan='Hà Nội', nghe_nghiep='Sinh viên')

    def post(self, **files):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(self.url, {**self.data, **files})

    def test_jpg_png_both_sides_and_reopen(self):
        self.assertRedirects(self.post(anh_giay_to_truoc=image_file(), anh_giay_to_sau=image_file('PNG')), self.url)
        profile = KhachThue.objects.get()
        for field, fmt, side in zip(IMAGE_FIELDS, ['JPEG', 'PNG'], ['truoc', 'sau']):
            with getattr(profile, field).open('rb') as file, Image.open(file) as picture:
                self.assertEqual(picture.format, fmt)
                self.assertEqual(picture.size, (800, 500))
            endpoint = reverse('anh_giay_to', args=[side])
            self.assertContains(self.client.get(self.url), endpoint)
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Cache-Control'], 'private, no-store')
            self.assertEqual(response['Content-Type'], 'image/jpeg' if fmt == 'JPEG' else 'image/png')
            response.close()

    def test_resize_above_1600_preserves_ratio(self):
        self.post(anh_giay_to_truoc=image_file(size=(2400, 1500)),
                  anh_giay_to_sau=image_file('PNG', size=(2000, 1000)))
        profile = KhachThue.objects.get()
        for field, expected in zip(IMAGE_FIELDS, [(1600, 1000), (1600, 800)]):
            with getattr(profile, field).open('rb') as file, Image.open(file) as picture:
                self.assertEqual(picture.size, expected)

    def test_no_upscale_at_or_below_1600(self):
        self.post(anh_giay_to_truoc=image_file(size=(1600, 900)),
                  anh_giay_to_sau=image_file('PNG', size=(600, 400)))
        profile = KhachThue.objects.get()
        for field, expected in zip(IMAGE_FIELDS, [(1600, 900), (600, 400)]):
            with getattr(profile, field).open('rb') as file, Image.open(file) as picture:
                self.assertEqual(picture.size, expected)

    def test_reject_other_formats_disguised_and_corrupt_images(self):
        for field in IMAGE_FIELDS:
            for make in [lambda: image_file('GIF', name='photo.gif'),
                         lambda: image_file('GIF', name='photo.jpg'),
                         lambda: image_file('PNG', name='photo.jpg'),
                         lambda: SimpleUploadedFile('photo.png', b'not an image'),
                         lambda: SimpleUploadedFile('photo.jpg', image_file().read()[:100])]:
                with self.subTest(field=field, case=make):
                    response = self.post(**{field: make()})
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(field, response.context['form'].errors)
                    self.assertFalse(KhachThue.objects.exists())
        self.assertEqual(list(self.media.rglob('*')), [])

    def test_each_image_over_5mb_rejected(self):
        for field in IMAGE_FIELDS:
            with self.subTest(field=field):
                upload = SimpleUploadedFile('large.jpg', b'x' * (MAX_IMAGE_BYTES + 1))
                response = self.post(**{field: upload})
                self.assertFormError(response.context['form'], field, 'Mỗi ảnh không được vượt quá 5MB.')
        self.assertFalse(KhachThue.objects.exists())

    def test_exactly_5mb_accepted(self):
        content = image_file().read()
        content += b'\0' * (MAX_IMAGE_BYTES - len(content))
        self.assertRedirects(self.post(anh_giay_to_truoc=SimpleUploadedFile('photo.JPG', content)), self.url)

    def test_invalid_back_keeps_existing_front_and_profile(self):
        self.post(anh_giay_to_truoc=image_file(), anh_giay_to_sau=image_file('PNG'))
        old = KhachThue.objects.get()
        names = [getattr(old, field).name for field in IMAGE_FIELDS]
        self.data['ho_ten'] = 'Tên chưa được lưu'
        response = self.post(anh_giay_to_truoc=image_file(size=(1000, 500)),
                             anh_giay_to_sau=SimpleUploadedFile('wrong.txt', b'wrong'))
        self.assertEqual(response.status_code, 200)
        old.refresh_from_db()
        self.assertEqual(old.ho_ten, 'Khách ảnh')
        self.assertEqual([getattr(old, field).name for field in IMAGE_FIELDS], names)
        self.assertEqual(len(list(self.media.rglob('*.*'))), 2)

    def test_replace_each_side_deletes_only_replaced_file(self):
        self.post(anh_giay_to_truoc=image_file(), anh_giay_to_sau=image_file('PNG'))
        for field in IMAGE_FIELDS:
            old = KhachThue.objects.get()
            old_path = getattr(old, field).path
            other_field = next(item for item in IMAGE_FIELDS if item != field)
            other_name = getattr(old, other_field).name
            self.assertRedirects(self.post(**{field: image_file('PNG')}), self.url)
            new = KhachThue.objects.get()
            self.assertFalse(Path(old_path).exists())
            self.assertTrue(Path(getattr(new, field).path).exists())
            self.assertEqual(getattr(new, other_field).name, other_name)
        self.assertEqual(KhachThue.objects.count(), 1)

    def test_edit_text_without_upload_keeps_images(self):
        self.post(anh_giay_to_truoc=image_file(), anh_giay_to_sau=image_file('PNG'))
        names = [getattr(KhachThue.objects.get(), field).name for field in IMAGE_FIELDS]
        self.data['nghe_nghiep'] = 'Kỹ sư'
        self.assertRedirects(self.post(), self.url)
        profile = KhachThue.objects.get()
        self.assertEqual([getattr(profile, field).name for field in IMAGE_FIELDS], names)
        self.assertEqual(profile.nghe_nghiep, 'Kỹ sư')

    def test_images_private_and_cannot_select_other_owner(self):
        self.post(anh_giay_to_truoc=image_file())
        profile = KhachThue.objects.get()
        endpoint = reverse('anh_giay_to', args=['truoc'])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(endpoint, {'tai_khoan': self.user.pk}).status_code, 404)
        self.assertEqual(self.client.get('/media/' + profile.anh_giay_to_truoc.name).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(endpoint).status_code, 302)
        self.other.vai_tro = VaiTro.CHU_NHA
        self.other.save()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(endpoint).status_code, 403)

    def test_failed_database_save_cleans_new_files(self):
        with patch('accounts.models.KhachThue.objects.update_or_create', side_effect=DatabaseError):
            response = self.post(anh_giay_to_truoc=image_file(), anh_giay_to_sau=image_file('PNG'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Không thể lưu hồ sơ lúc này.')
        self.assertFalse(KhachThue.objects.exists())
        self.assertFalse(any(path.is_file() for path in self.media.rglob('*')))

    def test_missing_file_returns_404(self):
        KhachThue.objects.create(tai_khoan=self.user, **self.data, anh_giay_to_truoc='giay-to/missing.jpg')
        self.assertEqual(self.client.get(reverse('anh_giay_to', args=['truoc'])).status_code, 404)
