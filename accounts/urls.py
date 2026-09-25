from django.urls import path
from . import views

urlpatterns = [
    path('dang-ky/', views.dang_ky_view, name='dang_ky'),
    path('dang-nhap/', views.dang_nhap_view, name='dang_nhap'),
    path('dang-xuat/', views.dang_xuat_view, name='dang_xuat'),
    path('trang-chu/', views.trang_chu_view, name='trang_chu'),
    path('', views.dang_ky_view, name='home'),
]
