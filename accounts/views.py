import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
from .forms import DangKyForm
from .models import TaiKhoan
from .tokens import (
    create_tokens_for_user,
    verify_access_token,
    refresh_access_token,
    revoke_tokens,
)


def dang_ky_view(request):
    """
    Xử lý hiển thị biểu mẫu và tiếp nhận đăng ký tài khoản khách thuê (S1-01).
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
                tokens = create_tokens_for_user(user)

                messages.success(request, 'Đăng ký thành công.')
                response = redirect('trang_chu')

                # Lưu token vào cookie để hỗ trợ duy trì phiên
                response.set_cookie('access_token', tokens['access_token'], max_age=1800, httponly=False)
                response.set_cookie('refresh_token', tokens['refresh_token'], max_age=604800, httponly=False)
                return response

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


def dang_nhap_view(request):
    """
    Màn hình đăng nhập khách thuê (S1-02).
    - Hỗ trợ đăng nhập bằng Email hoặc Số điện thoại cùng Mật khẩu.
    - Chống dò mật khẩu: Khóa tài khoản 15 phút khi nhập sai 5 lần trong 15 phút.
    - Hiển thị thời gian còn lại giảm dần theo thời gian thực khi bị khóa.
    - Sinh và cấp phát Access Token (30 phút) & Refresh Token (7 ngày).
    """
    if request.user.is_authenticated:
        return redirect('trang_chu')

    error_message = None
    lock_seconds = 0
    email_or_phone_val = ''

    if request.method == 'POST':
        email_or_phone_val = request.POST.get('email_or_phone', '').strip()
        mat_khau = request.POST.get('mat_khau', '')

        # Tìm user theo email hoặc số điện thoại
        lookup = email_or_phone_val.lower()
        if '@' in lookup:
            user_obj = TaiKhoan.objects.filter(email=lookup).first()
        else:
            user_obj = TaiKhoan.objects.filter(so_dien_thoai=email_or_phone_val).first()

        if not user_obj:
            # Không phân biệt sai tài khoản hay sai mật khẩu (chống dò tài khoản)
            error_message = 'Thông tin đăng nhập không chính xác.'
        else:
            # 1. Kiểm tra trạng thái tạm khóa (S1-02 Task 2)
            if user_obj.is_locked():
                lock_seconds = user_obj.get_remaining_lock_seconds()
                error_message = f'Tài khoản tạm thời bị khóa do nhập sai mật khẩu 5 lần liên tiếp. Vui lòng thử lại sau.'
            else:
                # Nếu đã hết thời gian khóa nhưng cờ còn lưu thì reset
                if user_obj.khoa_den:
                    user_obj.reset_login_failures()

                # 2. Xác thực mật khẩu
                if user_obj.check_password(mat_khau):
                    if not user_obj.is_active:
                        error_message = 'Tài khoản của bạn hiện đang bị khóa bởi quản trị viên.'
                    else:
                        # Đăng nhập thành công -> Đặt lại số lần sai
                        user_obj.reset_login_failures()
                        login(request, user_obj)

                        # Sinh access token (30 phút) và refresh token (7 ngày)
                        tokens = create_tokens_for_user(user_obj)

                        messages.success(request, f'Chào mừng {user_obj.ho_ten} quay trở lại!')
                        next_url = request.GET.get('next', 'trang_chu')
                        response = redirect(next_url)

                        # Lưu token vào cookie
                        response.set_cookie('access_token', tokens['access_token'], max_age=1800, httponly=False)
                        response.set_cookie('refresh_token', tokens['refresh_token'], max_age=604800, httponly=False)
                        return response
                else:
                    # Ghi nhận lần nhập sai mật khẩu
                    user_obj.record_login_failure()
                    if user_obj.is_locked():
                        lock_seconds = user_obj.get_remaining_lock_seconds()
                        error_message = f'Tài khoản đã bị tạm khóa 15 phút do nhập sai mật khẩu 5 lần liên tiếp.'
                    else:
                        error_message = 'Thông tin đăng nhập không chính xác.'

    return render(request, 'accounts/dang_nhap.html', {
        'error_message': error_message,
        'lock_seconds': lock_seconds,
        'email_or_phone': email_or_phone_val,
    })


@login_required
def trang_chu_view(request):
    """
    Trang đích sau khi đăng nhập thành công.
    Chỉ cho phép tài khoản đã xác thực truy cập; hiển thị họ tên và vai trò.
    """
    return render(request, 'accounts/dashboard.html', {
        'user': request.user,
        'active_nav': 'dashboard',
    })


def dang_xuat_view(request):
    """
    Đăng xuất tài khoản khách thuê (S1-02 Task 3).
    - Vô hiệu hóa refresh token và access token.
    - Xóa token khỏi thiết bị (cookie).
    - Hủy phiên đăng nhập Django session.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    access_token = request.COOKIES.get('access_token')

    if request.user.is_authenticated:
        revoke_tokens(refresh_token_str=refresh_token, access_token_str=access_token, user=request.user)
    elif refresh_token or access_token:
        revoke_tokens(refresh_token_str=refresh_token, access_token_str=access_token)

    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')

    response = redirect('dang_nhap')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


# ==============================================================================
# API ENDPOINTS CHO TOKEN VÀ BẢO VỆ PHIÊN (S1-02 AC1, AC2, AC3, AC4)
# ==============================================================================

@csrf_exempt
def api_login_view(request):
    """
    POST /api/auth/login/
    Tiếp nhận thông tin đăng nhập, trả về access token (30m) & refresh token (7d).
    Kiểm tra và xử lý khóa tài khoản 15 phút nếu sai 5 lần.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Phương thức không được hỗ trợ.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    email_or_phone = str(data.get('email_or_phone', '')).strip()
    mat_khau = str(data.get('mat_khau', ''))

    if not email_or_phone or not mat_khau:
        return JsonResponse({'error': 'Vui lòng nhập đầy đủ thông tin đăng nhập.'}, status=400)

    lookup = email_or_phone.lower()
    if '@' in lookup:
        user = TaiKhoan.objects.filter(email=lookup).first()
    else:
        user = TaiKhoan.objects.filter(so_dien_thoai=email_or_phone).first()

    if not user:
        return JsonResponse({'error': 'Thông tin đăng nhập không chính xác.'}, status=400)

    # 1. Kiểm tra tài khoản có bị khóa chống dò mật khẩu không
    if user.is_locked():
        lock_seconds = user.get_remaining_lock_seconds()
        return JsonResponse({
            'error': f'Tài khoản tạm thời bị khóa do nhập sai mật khẩu 5 lần. Vui lòng thử lại sau {lock_seconds} giây.',
            'is_locked': True,
            'lock_seconds_remaining': lock_seconds,
        }, status=423)

    if user.khoa_den:
        user.reset_login_failures()

    # 2. Kiểm tra mật khẩu
    if not user.check_password(mat_khau):
        user.record_login_failure()
        if user.is_locked():
            lock_seconds = user.get_remaining_lock_seconds()
            return JsonResponse({
                'error': f'Tài khoản đã bị tạm khóa 15 phút do nhập sai mật khẩu 5 lần liên tiếp.',
                'is_locked': True,
                'lock_seconds_remaining': lock_seconds,
            }, status=423)
        return JsonResponse({'error': 'Thông tin đăng nhập không chính xác.'}, status=400)

    if not user.is_active:
        return JsonResponse({'error': 'Tài khoản của bạn đã bị khóa bởi quản trị viên.'}, status=403)

    # Đăng nhập thành công -> Reset số lần sai
    user.reset_login_failures()
    tokens = create_tokens_for_user(user)

    return JsonResponse({
        'success': True,
        'message': 'Đăng nhập thành công.',
        'tokens': tokens,
        'user': {
            'id': user.id,
            'ho_ten': user.ho_ten,
            'email': user.email,
            'so_dien_thoai': user.so_dien_thoai,
            'vai_tro': user.vai_tro,
        }
    })


@csrf_exempt
def api_refresh_view(request):
    """
    POST /api/auth/refresh/
    Đổi refresh token còn hạn lấy access token mới (30 phút).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Phương thức không được hỗ trợ.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    refresh_token = data.get('refresh_token') or request.COOKIES.get('refresh_token')

    if not refresh_token:
        return JsonResponse({'error': 'Refresh token là bắt buộc.'}, status=401)

    try:
        token_info = refresh_access_token(refresh_token)
        response = JsonResponse(token_info)
        response.set_cookie('access_token', token_info['access_token'], max_age=token_info['expires_in'], httponly=False, samesite='Lax')
        return response
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=401)


@csrf_exempt
def api_logout_view(request):
    """
    POST /api/auth/logout/
    Vô hiệu hóa refresh token và access token khi người dùng đăng xuất.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Phương thức không được hỗ trợ.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    refresh_token = data.get('refresh_token') or request.COOKIES.get('refresh_token')
    auth_header = request.headers.get('Authorization', '')
    access_token = None
    if auth_header.startswith('Bearer '):
        access_token = auth_header[7:].strip()
    elif 'access_token' in request.COOKIES:
        access_token = request.COOKIES.get('access_token')

    user = None
    if access_token:
        user = verify_access_token(access_token)

    revoke_tokens(refresh_token_str=refresh_token, access_token_str=access_token, user=user)

    if request.user.is_authenticated:
        logout(request)

    response = JsonResponse({'success': True, 'message': 'Đăng xuất thành công và vô hiệu hóa phiên làm việc.'})
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


def api_me_view(request):
    """
    GET /api/auth/me/
    Endpoint mẫu yêu cầu xác thực bằng Access Token qua Header:
    Authorization: Bearer <access_token>
    Dùng để kiểm thử gọi API bằng token cũ sau đăng xuất trả về mã 401.
    """
    auth_header = request.headers.get('Authorization', '')
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()
    elif 'access_token' in request.COOKIES:
        token = request.COOKIES.get('access_token')

    if not token:
        return JsonResponse({'error': 'Không có token xác thực.'}, status=401)

    user = verify_access_token(token)
    if not user:
        return JsonResponse({'error': 'Token không hợp lệ, đã hết hạn hoặc đã bị vô hiệu hóa sau đăng xuất.'}, status=401)

    return JsonResponse({
        'id': user.id,
        'ho_ten': user.ho_ten,
        'email': user.email,
        'so_dien_thoai': user.so_dien_thoai,
        'vai_tro': user.vai_tro,
    })
