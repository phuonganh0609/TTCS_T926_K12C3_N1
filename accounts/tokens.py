import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
import jwt
from django.conf import settings
from django.utils import timezone
from .models import TaiKhoan, PhienDangNhap, ThuHoiAccessToken

ACCESS_TOKEN_LIFETIME = timedelta(minutes=30)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)


def create_tokens_for_user(user):
    """
    Sinh access token (30 phút) và refresh token (7 ngày) khi xác thực thành công.
    Lưu phiên đăng nhập refresh token vào CSDL.
    """
    now = timezone.now()
    access_jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())

    access_exp = now + ACCESS_TOKEN_LIFETIME
    refresh_exp = now + REFRESH_TOKEN_LIFETIME

    access_payload = {
        'user_id': user.id,
        'email': user.email,
        'so_dien_thoai': user.so_dien_thoai,
        'vai_tro': user.vai_tro,
        'ho_ten': user.ho_ten,
        'jti': access_jti,
        'token_type': 'access',
        # Preserve sub-second precision so a token issued immediately after
        # logout is not mistaken for a token issued before it.
        'iat': now.timestamp(),
        'exp': int(access_exp.timestamp()),
    }

    refresh_payload = {
        'user_id': user.id,
        'jti': refresh_jti,
        'token_type': 'refresh',
        'iat': int(now.timestamp()),
        'exp': int(refresh_exp.timestamp()),
    }

    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

    # Lưu refresh token vào CSDL để quản lý phiên và thu hồi
    PhienDangNhap.objects.create(
        tai_khoan=user,
        token_id=refresh_jti,
        ngay_het_han=refresh_exp,
    )

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': int(ACCESS_TOKEN_LIFETIME.total_seconds()),
        'refresh_expires_in': int(REFRESH_TOKEN_LIFETIME.total_seconds()),
    }


def verify_access_token(token_str):
    """
    Xác thực access token.
    Kiểm tra hạn sử dụng, tính hợp lệ, trạng thái thu hồi sau đăng xuất.
    Trả về instance TaiKhoan hoặc None.
    """
    if not token_str:
        return None

    try:
        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

    if payload.get('token_type') != 'access':
        return None

    jti = payload.get('jti')
    # Kiểm tra trong bảng token bị thu hồi
    if ThuHoiAccessToken.objects.filter(jti=jti).exists():
        return None

    user = TaiKhoan.objects.filter(id=payload.get('user_id')).first()
    if not user or not user.is_active:
        return None

    # Nếu token được tạo trước thời điểm đăng xuất gần nhất của người dùng
    if user.thoi_diem_dang_xuat:
        token_iat = payload.get('iat', 0)
        logout_ts = user.thoi_diem_dang_xuat.timestamp()
        if token_iat <= logout_ts:
            return None

    return user


def refresh_access_token(refresh_token_str):
    """
    Đổi refresh token còn hạn lấy access token mới (30 phút).
    Từ chối nếu token hết hạn hoặc đã bị thu hồi.
    """
    if not refresh_token_str:
        raise ValueError('Refresh token là bắt buộc.')

    try:
        payload = jwt.decode(refresh_token_str, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise ValueError('Refresh token đã hết hạn.')
    except jwt.InvalidTokenError:
        raise ValueError('Refresh token không hợp lệ.')

    if payload.get('token_type') != 'refresh':
        raise ValueError('Loại token không phải refresh token.')

    jti = payload.get('jti')
    phien = PhienDangNhap.objects.filter(token_id=jti).select_related('tai_khoan').first()

    if not phien:
        raise ValueError('Phiên đăng nhập không tồn tại.')

    if not phien.is_valid():
        raise ValueError('Phiên đăng nhập đã hết hạn hoặc đã bị vô hiệu hóa.')

    user = phien.tai_khoan
    if not user.is_active:
        raise ValueError('Tài khoản đã bị khóa.')

    # Sinh access token mới
    now = timezone.now()
    access_jti = str(uuid.uuid4())
    access_exp = now + ACCESS_TOKEN_LIFETIME

    access_payload = {
        'user_id': user.id,
        'email': user.email,
        'so_dien_thoai': user.so_dien_thoai,
        'vai_tro': user.vai_tro,
        'ho_ten': user.ho_ten,
        'jti': access_jti,
        'token_type': 'access',
        'iat': now.timestamp(),
        'exp': int(access_exp.timestamp()),
    }

    new_access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')

    return {
        'access_token': new_access_token,
        'token_type': 'Bearer',
        'expires_in': int(ACCESS_TOKEN_LIFETIME.total_seconds()),
    }


def revoke_tokens(refresh_token_str=None, access_token_str=None, user=None):
    """
    Vô hiệu hóa refresh token và access token khi người dùng đăng xuất.
    """
    now = timezone.now()

    # 1. Thu hồi refresh token cụ thể nếu được truyền
    if refresh_token_str:
        try:
            payload = jwt.decode(refresh_token_str, settings.SECRET_KEY, algorithms=['HS256'], options={'verify_exp': False})
            jti = payload.get('jti')
            PhienDangNhap.objects.filter(token_id=jti).update(da_thu_hoi=True)
            if not user:
                user_id = payload.get('user_id')
                user = TaiKhoan.objects.filter(id=user_id).first()
        except jwt.PyJWTError:
            pass

    # 2. Thu hồi access token cụ thể
    if access_token_str:
        try:
            payload = jwt.decode(access_token_str, settings.SECRET_KEY, algorithms=['HS256'], options={'verify_exp': False})
            jti = payload.get('jti')
            exp_ts = payload.get('exp')
            exp_dt = datetime.fromtimestamp(exp_ts, tz=dt_timezone.utc) if exp_ts else (now + ACCESS_TOKEN_LIFETIME)
            ThuHoiAccessToken.objects.get_or_create(jti=jti, defaults={'ngay_het_han': exp_dt})
            if not user:
                user_id = payload.get('user_id')
                user = TaiKhoan.objects.filter(id=user_id).first()
        except jwt.PyJWTError:
            pass

    # 3. Cập nhật thời điểm đăng xuất của người dùng và thu hồi mọi phiên đang mở
    if user:
        user.thoi_diem_dang_xuat = now
        user.save(update_fields=['thoi_diem_dang_xuat'])
        PhienDangNhap.objects.filter(tai_khoan=user, da_thu_hoi=False).update(da_thu_hoi=True)
