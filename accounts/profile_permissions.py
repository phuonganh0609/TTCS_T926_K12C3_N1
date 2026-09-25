"""Phân quyền tại backend trước khi chuyển dữ liệu hồ sơ sang giao diện."""
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from .models import HopDong, VaiTro


def mask_identity(number):
    return '*' * max(0, len(number) - 4) + number[-4:]


def can_view_full_identity(viewer, profile):
    if not viewer.is_authenticated or not viewer.is_active:
        return False
    if viewer.vai_tro == VaiTro.ADMIN:
        return True
    if viewer.vai_tro != VaiTro.CHU_NHA:
        return False
    today = timezone.localdate()
    return HopDong.objects.filter(
        khach_dung_ten_id=profile.pk,
        phong__toa_nha__chu_nha_id=viewer.pk,
        trang_thai=HopDong.TrangThai.DANG_HIEU_LUC,
        cac_ky__ngay_bat_dau__lte=today,
        cac_ky__ngay_ket_thuc__gte=today,
    ).filter(Q(ngay_tra_phong__isnull=True) | Q(ngay_tra_phong__gte=today)).exists()


def can_view_identity_images(viewer, profile):
    return viewer.is_authenticated and viewer.is_active and (
        (viewer.pk == profile.tai_khoan_id and viewer.vai_tro == VaiTro.KHACH_THUE)
        or can_view_full_identity(viewer, profile)
    )


def profile_for_display(viewer, profile):
    """Chỉ chuyển dữ liệu đã phân quyền; không chuyển model thô vào trang xem."""
    full = can_view_full_identity(viewer, profile)
    images_allowed = can_view_identity_images(viewer, profile)
    return {
        'id': profile.pk,
        'ho_ten': profile.ho_ten,
        'ngay_sinh': profile.ngay_sinh,
        'que_quan': profile.que_quan,
        'nghe_nghiep': profile.nghe_nghiep,
        'so_giay_to': profile.so_giay_to if full else mask_identity(profile.so_giay_to),
        'can_view_full_identity': full,
        'can_edit': viewer.pk == profile.tai_khoan_id and viewer.vai_tro == VaiTro.KHACH_THUE,
        'images_allowed': images_allowed,
        'anh_truoc': reverse('anh_ho_so', args=[profile.pk, 'truoc'])
        if images_allowed and profile.anh_giay_to_truoc else None,
        'anh_sau': reverse('anh_ho_so', args=[profile.pk, 'sau'])
        if images_allowed and profile.anh_giay_to_sau else None,
    }
