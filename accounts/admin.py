from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import TaiKhoan, VaiTro, ToaNha, PhongTro, HopDong, KyHopDong


@admin.register(TaiKhoan)
class TaiKhoanAdmin(BaseUserAdmin):
    list_display = ('ho_ten', 'email', 'so_dien_thoai', 'vai_tro', 'is_active', 'ngay_tao')
    list_filter = ('vai_tro', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('ho_ten', 'email', 'so_dien_thoai')
    ordering = ('-ngay_tao',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Thông tin cá nhân', {'fields': ('ho_ten', 'so_dien_thoai', 'vai_tro')}),
        ('Quyền hạn', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Thời gian', {'fields': ('last_login', 'ngay_tao', 'ngay_cap_nhat')}),
    )
    readonly_fields = ('ngay_tao', 'ngay_cap_nhat', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'so_dien_thoai', 'ho_ten', 'password', 'vai_tro'),
        }),
    )


class RentalRelationAdmin(admin.ModelAdmin):
    """Chỉ quản trị được cấp quyền Django mới chỉnh quan hệ dùng phân quyền."""
    def has_module_permission(self, request):
        return request.user.vai_tro == VaiTro.ADMIN and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return request.user.vai_tro == VaiTro.ADMIN and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return request.user.vai_tro == VaiTro.ADMIN and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.vai_tro == VaiTro.ADMIN and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return request.user.vai_tro == VaiTro.ADMIN and super().has_delete_permission(request, obj)


@admin.register(ToaNha)
class ToaNhaAdmin(RentalRelationAdmin):
    list_display = ('ten_toa_nha', 'chu_nha')


@admin.register(PhongTro)
class PhongTroAdmin(RentalRelationAdmin):
    list_display = ('ma_phong', 'toa_nha')


@admin.register(HopDong)
class HopDongAdmin(RentalRelationAdmin):
    list_display = ('ma_hop_dong', 'phong', 'khach_dung_ten', 'trang_thai', 'ngay_tra_phong')


@admin.register(KyHopDong)
class KyHopDongAdmin(RentalRelationAdmin):
    list_display = ('hop_dong', 'so_thu_tu', 'ngay_bat_dau', 'ngay_ket_thuc')
