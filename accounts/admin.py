from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import TaiKhoan


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
