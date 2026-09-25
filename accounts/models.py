import re
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.core.exceptions import ValidationError
from django.utils import timezone


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

    # Quản lý khóa tài khoản khi sai mật khẩu liên tiếp (S1-02 Task 2)
    so_lan_sai = models.IntegerField(default=0, verbose_name='Số lần đăng nhập sai')
    khoa_den = models.DateTimeField(null=True, blank=True, verbose_name='Khóa đăng nhập đến')
    lan_sai_cuoi = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm sai gần nhất')
    thoi_diem_dang_xuat = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm đăng xuất gần nhất')

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

    def is_locked(self):
        """Kiểm tra tài khoản có đang trong thời gian bị tạm khóa đăng nhập không."""
        if self.khoa_den and self.khoa_den > timezone.now():
            return True
        return False

    def get_remaining_lock_seconds(self):
        """Trả về số giây còn lại đang bị khóa (hoặc 0 nếu không bị khóa)."""
        if self.is_locked():
            diff = (self.khoa_den - timezone.now()).total_seconds()
            return max(0, int(diff))
        return 0

    def record_login_failure(self):
        """
        Ghi nhận một lần đăng nhập sai.
        - Đếm số lần sai trong vòng 15 phút.
        - Nếu đạt 5 lần trong 15 phút -> khóa 15 phút.
        """
        now = timezone.now()
        # Nếu lần sai trước đó đã quá 15 phút thì đặt lại số lần sai về 1
        if self.lan_sai_cuoi and (now - self.lan_sai_cuoi) > timedelta(minutes=15):
            self.so_lan_sai = 1
        else:
            self.so_lan_sai += 1

        self.lan_sai_cuoi = now

        # Đạt 5 lần sai trong vòng 15 phút -> khóa 15 phút
        if self.so_lan_sai >= 5:
            self.khoa_den = now + timedelta(minutes=15)

        self.save(update_fields=['so_lan_sai', 'lan_sai_cuoi', 'khoa_den'])

    def reset_login_failures(self):
        """Đặt lại số lần đăng nhập sai khi đăng nhập thành công hoặc hết hạn khóa."""
        self.so_lan_sai = 0
        self.khoa_den = None
        self.lan_sai_cuoi = None
        self.save(update_fields=['so_lan_sai', 'khoa_den', 'lan_sai_cuoi'])

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


class PhienDangNhap(models.Model):
    """
    Quản lý Refresh Token và phiên làm việc (S1-02 Task 1 & Task 3).
    Hạn sử dụng 7 ngày. Hỗ trợ thu hồi (vô hiệu hóa) khi đăng xuất.
    """
    tai_khoan = models.ForeignKey(TaiKhoan, on_delete=models.CASCADE, related_name='phien_dang_nhap')
    token_id = models.CharField(max_length=64, unique=True, db_index=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_het_han = models.DateTimeField()
    da_thu_hoi = models.BooleanField(default=False)

    class Meta:
        db_table = 'phien_dang_nhap'
        verbose_name = 'Phiên đăng nhập'
        verbose_name_plural = 'Danh sách phiên đăng nhập'

    def is_valid(self):
        return not self.da_thu_hoi and self.ngay_het_han > timezone.now()


class ThuHoiAccessToken(models.Model):
    """
    Danh sách các Access Token bị thu hồi trước hạn (Blacklist sau khi đăng xuất).
    """
    jti = models.CharField(max_length=64, unique=True, db_index=True)
    ngay_het_han = models.DateTimeField()
    ngay_thu_hoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'thu_hoi_access_token'
        verbose_name = 'Access Token bị thu hồi'
        verbose_name_plural = 'Danh sách Access Token bị thu hồi'
