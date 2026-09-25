import re
from django import forms
from django.core.exceptions import ValidationError
from .models import TaiKhoan, VaiTro, KhachThue
from .profile_images import IMAGE_FIELDS, prepare_identity_image


class IdentityImageField(forms.FileField):
    def clean(self, data, initial=None):
        value = super().clean(data, initial)
        return prepare_identity_image(data) if data else value


class HoSoKhachThueForm(forms.ModelForm):
    anh_giay_to_truoc = IdentityImageField(
        label='Ảnh mặt trước', required=False,
        widget=forms.FileInput(attrs={'accept': '.jpg,.jpeg,.png,image/jpeg,image/png'}),
    )
    anh_giay_to_sau = IdentityImageField(
        label='Ảnh mặt sau', required=False,
        widget=forms.FileInput(attrs={'accept': '.jpg,.jpeg,.png,image/jpeg,image/png'}),
    )
    # Không tự xóa khoảng trắng hay ký tự sai trong số căn cước.
    so_giay_to = forms.RegexField(
        label='Số căn cước', regex=r'\A(?:[0-9]{9}|[0-9]{12})\Z', strip=False,
        error_messages={
            'required': 'Vui lòng nhập số căn cước.',
            'invalid': 'Số căn cước chỉ được gồm 9 hoặc 12 chữ số.',
        },
        widget=forms.PasswordInput(render_value=False, attrs={
            'inputmode': 'numeric', 'pattern': '[0-9]{9}|[0-9]{12}',
            'aria-describedby': 'can-cuoc-help id_so_giay_to_errors',
        }),
    )

    class Meta:
        model = KhachThue
        fields = ['ho_ten', 'ngay_sinh', 'so_giay_to', 'que_quan', 'nghe_nghiep', *IMAGE_FIELDS]
        widgets = {
            'ngay_sinh': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }
        error_messages = {
            field: {'required': 'Vui lòng điền thông tin này.'}
            for field in ['ho_ten', 'ngay_sinh', 'que_quan', 'nghe_nghiep']
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_identity = self.instance.so_giay_to if self.instance.pk else ''
        # Không đưa số cũ vào value, hidden field hoặc dữ liệu initial của form.
        self.initial['so_giay_to'] = ''
        if self._saved_identity:
            self.fields['so_giay_to'].required = False
            self.fields['so_giay_to'].help_text = 'Để trống để giữ số đã lưu. Chỉ nhập khi cần thay đổi.'
        self.fields['so_giay_to'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['ngay_sinh'].input_formats = ['%Y-%m-%d']
        self.fields['ngay_sinh'].error_messages['invalid'] = 'Ngày sinh không hợp lệ.'
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs.setdefault('aria-describedby', f'id_{name}_errors')
        if self.is_bound:
            for name in self.errors:
                if name in self.fields:
                    self.fields[name].widget.attrs.update({
                        'class': 'form-control is-invalid', 'aria-invalid': 'true',
                    })

    @property
    def text_fields(self):
        return [self[name] for name in self.fields if name not in IMAGE_FIELDS]

    @property
    def image_fields(self):
        return [self[name] for name in IMAGE_FIELDS]

    def clean_so_giay_to(self):
        return self.cleaned_data['so_giay_to'] or self._saved_identity


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
