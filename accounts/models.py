import re
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.core.exceptions import ValidationError


class VaiTro(models.TextChoices):
    KHACH_THUE = 'KHACH_THUE', 'Khách thuê'
    CHU_NHA = 'CHU_NHA', 'Chủ nhà'
    QUAN_LY = 'QUAN_LY', 'Quản lý tòa nhà'
    ADMIN = 'ADMIN', 'Quản trị hệ thống'


class TaiKhoanManager(BaseUserManager):
    """
    Trình quản lý tài khoản hỗ trợ chuẩn hóa email, số điện thoại
    và thiết lập mật khẩu băm đúng hasher BCrypt đã cấu hình.
    """
    def create_user(self, email, so_dien_thoai, ho_ten, password=None, **extra_fields):
        if not email:
            raise ValueError('Email là bắt buộc.')
        if not so_dien_thoai:
            raise ValueError('Số điện thoại là bắt buộc.')
        if not ho_ten:
            raise ValueError('Họ tên là bắt buộc.')

        # Chuẩn hóa email lowercase + strip theo quy tắc nghiệp vụ
        email = self.normalize_email(email).strip().lower()
        so_dien_thoai = str(so_dien_thoai).strip()
        ho_ten = str(ho_ten).strip()

        extra_fields.setdefault('vai_tro', VaiTro.KHACH_THUE)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        user = self.model(
            email=email,
            so_dien_thoai=so_dien_thoai,
            ho_ten=ho_ten,
            **extra_fields
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, so_dien_thoai, ho_ten, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('vai_tro', VaiTro.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser phải có is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser phải có is_superuser=True.')

        return self.create_user(email, so_dien_thoai, ho_ten, password, **extra_fields)


class TaiKhoan(AbstractBaseUser, PermissionsMixin):
    """
    Bảng tai_khoan theo đặc tả CSDL (22 bảng), đóng vai trò Custom User
    ngay từ migration đầu tiên của Django.
    """
    # Ánh xạ cột password vào mat_khau trong CSDL
    password = models.CharField(max_length=128, db_column='mat_khau')

    ho_ten = models.CharField(max_length=100, verbose_name='Họ và tên')
    email = models.EmailField(max_length=254, unique=True, verbose_name='Địa chỉ Email')
    so_dien_thoai = models.CharField(max_length=10, unique=True, verbose_name='Số điện thoại')

    vai_tro = models.CharField(
        max_length=20,
        choices=VaiTro.choices,
        default=VaiTro.KHACH_THUE,
        verbose_name='Vai trò',
    )

    # Ánh xạ is_active vào dang_hoat_dong trong CSDL
    is_active = models.BooleanField(
        default=True,
        db_column='dang_hoat_dong',
        verbose_name='Đang hoạt động',
    )
    is_staff = models.BooleanField(default=False, verbose_name='Nhân viên hệ thống')

    # last_login và is_superuser đã được kế thừa từ AbstractBaseUser & PermissionsMixin
    ngay_tao = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    ngay_cap_nhat = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    objects = TaiKhoanManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['ho_ten', 'so_dien_thoai']

    class Meta:
        db_table = 'tai_khoan'
        verbose_name = 'Tài khoản'
        verbose_name_plural = 'Danh sách tài khoản'
        indexes = [
            models.Index(fields=['vai_tro', 'is_active'], name='idx_tk_vaitro_hoatdong'),
        ]

    @property
    def dang_hoat_dong(self):
        return self.is_active

    @dang_hoat_dong.setter
    def dang_hoat_dong(self, value):
        self.is_active = value

    @property
    def mat_khau(self):
        return self.password

    @mat_khau.setter
    def mat_khau(self, raw_password):
        self.set_password(raw_password)

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()
        if self.so_dien_thoai:
            self.so_dien_thoai = str(self.so_dien_thoai).strip()
            if not re.match(r'^0[0-9]{9}$', self.so_dien_thoai):
                raise ValidationError({
                    'so_dien_thoai': 'Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0.'
                })

    def __str__(self):
        return f"{self.ho_ten} ({self.email}) - {self.get_vai_tro_display()}"
