from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from .forms import DangKyForm
from .models import TaiKhoan


def dang_ky_view(request):
    """
    Xử lý hiển thị biểu mẫu và tiếp nhận đăng ký tài khoản khách thuê (S1-01).
    - Tạo tài khoản hợp lệ, băm mật khẩu bằng BCrypt, gán vai trò Khách thuê.
    - Ngăn trùng lặp số điện thoại và email với thông báo tương ứng.
    - Bắt IntegrityError tránh lỗi 500 khi có tranh chấp đồng thời tại DB.
    - Tự động đăng nhập và chuyển hướng tới trang đích sau khi thành công.
    """
    if request.user.is_authenticated:
        return redirect('trang_chu')

    if request.method == 'POST':
        form = DangKyForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()

                # Tự động đăng nhập bằng Django session
                login(request, user)
                messages.success(request, 'Đăng ký thành công.')
                return redirect('trang_chu')

            except IntegrityError:
                # Xử lý xung đột đồng thời tại mức DB UNIQUE constraint
                so_dien_thoai = form.cleaned_data.get('so_dien_thoai')
                email = form.cleaned_data.get('email')

                has_conflict = False
                if so_dien_thoai and TaiKhoan.objects.filter(so_dien_thoai=so_dien_thoai).exists():
                    form.add_error('so_dien_thoai', 'Số điện thoại này đã được sử dụng.')
                    has_conflict = True

                if email and TaiKhoan.objects.filter(email=email).exists():
                    form.add_error('email', 'Email này đã được sử dụng.')
                    has_conflict = True

                if not has_conflict:
                    form.add_error(None, 'Đã xảy ra lỗi khi tạo tài khoản. Vui lòng thử lại.')
    else:
        form = DangKyForm()

    return render(request, 'accounts/dang_ky.html', {'form': form})


@login_required
def trang_chu_view(request):
    """
    Trang đích sau khi đăng nhập thành công.
    Chỉ cho phép tài khoản đã xác thực truy cập; hiển thị họ tên và vai trò.
    """
    return render(request, 'accounts/dashboard.html', {
        'user': request.user,
    })


def dang_xuat_view(request):
    """
    Đăng xuất tài khoản và xóa phiên làm việc.
    """
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('dang_ky')


def dang_nhap_view(request):
    """
    Trang đăng nhập tối thiểu hỗ trợ kiểm thử và điều hướng khi chưa đăng nhập.
    """
    if request.user.is_authenticated:
        return redirect('trang_chu')

    error_message = None
    if request.method == 'POST':
        email_or_phone = request.POST.get('email_or_phone', '').strip().lower()
        mat_khau = request.POST.get('mat_khau', '')

        # Tìm user theo email hoặc số điện thoại
        user_obj = None
        if '@' in email_or_phone:
            user_obj = TaiKhoan.objects.filter(email=email_or_phone).first()
        else:
            user_obj = TaiKhoan.objects.filter(so_dien_thoai=email_or_phone).first()

        if user_obj and user_obj.check_password(mat_khau):
            if user_obj.is_active:
                login(request, user_obj)
                messages.success(request, f'Chào mừng {user_obj.ho_ten} quay trở lại!')
                next_url = request.GET.get('next', 'trang_chu')
                return redirect(next_url)
            else:
                error_message = 'Tài khoản của bạn hiện đang bị khóa.'
        else:
            error_message = 'Thông tin đăng nhập không chính xác.'

    return render(request, 'accounts/dang_nhap.html', {'error_message': error_message})
