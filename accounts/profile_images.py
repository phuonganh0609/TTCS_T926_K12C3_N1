"""Kiểm tra, chuẩn hóa và lưu ảnh giấy tờ trong vùng lưu trữ riêng."""
import logging
import warnings
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.db import transaction

MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_FIELDS = ('anh_giay_to_truoc', 'anh_giay_to_sau')
logger = logging.getLogger(__name__)


def prepare_identity_image(upload):
    if upload.size > MAX_IMAGE_BYTES:
        raise ValidationError('Mỗi ảnh không được vượt quá 5MB.')
    extension = Path(upload.name).suffix.lower()
    if extension not in {'.jpg', '.jpeg', '.png'}:
        raise ValidationError('Chỉ chấp nhận ảnh JPG hoặc PNG.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            upload.seek(0)
            with Image.open(upload) as probe:
                image_format = probe.format
                if image_format not in {'JPEG', 'PNG'}:
                    raise ValidationError('Chỉ chấp nhận ảnh JPG hoặc PNG.')
                if (image_format == 'PNG') != (extension == '.png'):
                    raise ValidationError('Định dạng ảnh không khớp với phần mở rộng của tệp.')
                probe.verify()
            upload.seek(0)
            with Image.open(upload) as source:
                source.load()
                picture = ImageOps.exif_transpose(source)
                if picture.width > 1600:
                    height = max(1, round(picture.height * 1600 / picture.width))
                    picture = picture.resize((1600, height), Image.Resampling.LANCZOS)
                picture = picture.convert('RGB' if image_format == 'JPEG' else 'RGBA')
                # Chỉ giữ pixel, loại bỏ metadata/EXIF và dữ liệu đính kèm.
                picture.info.clear()
                output = BytesIO()
                picture.save(output, format=image_format, **(
                    {'quality': 85, 'optimize': True} if image_format == 'JPEG'
                    else {'optimize': True}
                ))
        suffix = '.jpg' if image_format == 'JPEG' else '.png'
        return SimpleUploadedFile(uuid4().hex + suffix, output.getvalue(),
                                  content_type='image/jpeg' if image_format == 'JPEG' else 'image/png')
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError('Tệp ảnh không hợp lệ hoặc không thể đọc được.')
    finally:
        upload.seek(0)


def delete_stored_image(storage, name):
    try:
        storage.delete(name)
    except OSError:
        logger.warning('Không thể dọn tệp ảnh giấy tờ cũ.')


def save_profile(user, cleaned_data):
    from .models import KhachThue

    created_files = []
    try:
        with transaction.atomic():
            old = KhachThue.objects.select_for_update().filter(tai_khoan=user).first()
            values = {key: value for key, value in cleaned_data.items() if key not in IMAGE_FIELDS}
            replaced_files = []
            for field_name in IMAGE_FIELDS:
                upload = cleaned_data.get(field_name)
                # Không chọn tệp mới thì giữ ảnh hiện tại, kể cả khi sửa thông tin.
                if not isinstance(upload, UploadedFile):
                    continue
                field = KhachThue._meta.get_field(field_name)
                name = field.storage.save(field.generate_filename(old, upload.name), upload)
                created_files.append((field.storage, name))
                values[field_name] = name
                previous = getattr(old, field_name) if old else None
                if previous:
                    replaced_files.append((field.storage, previous.name))
            profile, _ = KhachThue.objects.update_or_create(tai_khoan=user, defaults=values)
            for storage, name in replaced_files:
                transaction.on_commit(lambda storage=storage, name=name: delete_stored_image(storage, name))
        return profile
    except Exception:
        for storage, name in created_files:
            delete_stored_image(storage, name)
        raise
