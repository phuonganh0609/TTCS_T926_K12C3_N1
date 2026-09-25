import re
from django import forms
from django.core.exceptions import ValidationError
from .models import TaiKhoan, VaiTro


class DangKyForm(forms.Form):
    """
    Biểu mẫu đăng ký tài khoản khách thuê (Story S1-01).
    Bao gồm 4 trường: họ tên, số điện thoại, email, mật khẩu.
    """
    ho_ten = forms.CharField(
        max_length=100,
        label='Họ và tên',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nguyễn Văn A',
            'autocomplete': 'name',
            'required': True,
        }),
        error_messages={
            'required': 'Vui lòng nhập họ và tên.',
            'max_length': 'Họ và tên không được vượt quá 100 ký tự.',
        }
    )

    so_dien_thoai = forms.CharField(
        max_length=10,
        label='Số điện thoại',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0912345678',
            'autocomplete': 'tel',
            'pattern': '^0[0-9]{9}$',
            'inputmode': 'numeric',
            'required': True,
        }),
        error_messages={
            'required': 'Vui lòng nhập số điện thoại.',
            'max_length': 'Số điện thoại phải gồm đúng 10 chữ số.',
        }
    )

    email = forms.EmailField(
        max_length=254,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@domain.com',
            'autocomplete': 'email',
            'required': True,
        }),
        error_messages={
            'required': 'Vui lòng nhập địa chỉ email.',
            'invalid': 'Địa chỉ email không đúng định dạng.',
        }
    )

    mat_khau = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tối thiểu 8 ký tự, gồm cả chữ và số',
            'autocomplete': 'new-password',
            'required': True,
        }),
        error_messages={
            'required': 'Vui lòng nhập mật khẩu.',
        }
    )

    def clean_ho_ten(self):
        ho_ten = self.cleaned_data.get('ho_ten', '').strip()
        if not ho_ten:
            raise ValidationError('Vui lòng nhập họ và tên.')
        return ho_ten

    def clean_so_dien_thoai(self):
        so_dien_thoai = self.cleaned_data.get('so_dien_thoai', '').strip()
        # Số điện thoại đúng 10 chữ số ASCII, bắt đầu bằng 0
        if not re.match(r'^0[0-9]{9}$', so_dien_thoai):
            raise ValidationError('Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0.')
        return so_dien_thoai

    def clean_email(self):
        # Chuẩn hóa email strip + lowercase nhất quán
        email = self.cleaned_data.get('email', '').strip().lower()
        return email

    def clean_mat_khau(self):
        # Mật khẩu lấy từ self.data để không bị vô tình strip hay biến đổi
        mat_khau = self.data.get('mat_khau', '')
        if len(mat_khau) < 8 or not re.search(r'[A-Za-z]', mat_khau) or not re.search(r'[0-9]', mat_khau):
            raise ValidationError('Mật khẩu phải có ít nhất 8 ký tự, gồm ít nhất một chữ cái và một chữ số.')
        return mat_khau

    def clean(self):
        cleaned_data = super().clean()
        so_dien_thoai = cleaned_data.get('so_dien_thoai')
        email = cleaned_data.get('email')

        # Task 2: Kiểm tra độc lập số điện thoại và email đã tồn tại
        # Trùng trường nào báo dưới trường đó; trùng cả hai hiện cả hai lỗi trong một lần gửi
        if so_dien_thoai and TaiKhoan.objects.filter(so_dien_thoai=so_dien_thoai).exists():
            self.add_error('so_dien_thoai', 'Số điện thoại này đã được sử dụng.')

        if email and TaiKhoan.objects.filter(email=email).exists():
            self.add_error('email', 'Email này đã được sử dụng.')

        return cleaned_data

    def save(self):
        """
        Tạo tài khoản người dùng với vai trò KHACH_THUE.
        Mật khẩu được băm an toàn qua BCryptSHA256PasswordHasher.
        """
        user = TaiKhoan(
            ho_ten=self.cleaned_data['ho_ten'],
            so_dien_thoai=self.cleaned_data['so_dien_thoai'],
            email=self.cleaned_data['email'],
            vai_tro=VaiTro.KHACH_THUE,
            is_staff=False,
            is_superuser=False,
        )
        # Băm mật khẩu bằng hasher chuẩn đã cấu hình
        user.set_password(self.cleaned_data['mat_khau'])
        user.save()
        return user
