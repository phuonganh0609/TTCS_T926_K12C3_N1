from django.urls import path
from . import views

urlpatterns = [
    path('ho-so/', views.ho_so_view, name='ho_so'),
    path('ho-so/khach-thue/', views.danh_sach_ho_so_view, name='danh_sach_ho_so'),
    path('ho-so/<int:pk>/', views.xem_ho_so_view, name='xem_ho_so'),
    path('ho-so/<int:pk>/anh/<str:mat>/', views.anh_giay_to_view, name='anh_ho_so'),
    path('ho-so/anh/<str:mat>/', views.anh_giay_to_view, name='anh_giay_to'),
    # Giao diện Web (Django Templates)
    path('dang-ky/', views.dang_ky_view, name='dang_ky'),
    path('dang-nhap/', views.dang_nhap_view, name='dang_nhap'),
    path('dang-xuat/', views.dang_xuat_view, name='dang_xuat'),
    path('trang-chu/', views.trang_chu_view, name='trang_chu'),
    path('', views.dang_ky_view, name='home'),

    # API Endpoints cho Token và Bảo vệ phiên (S1-02)
    path('api/auth/login/', views.api_login_view, name='api_login'),
    path('api/auth/refresh/', views.api_refresh_view, name='api_refresh'),
    path('api/auth/logout/', views.api_logout_view, name='api_logout'),
    path('api/auth/me/', views.api_me_view, name='api_me'),
]
