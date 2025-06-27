# SHA_GROUP/sha/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('request-otp/', views.RequestPhoneOTP.as_view(), name='request_otp'),
    path('verify-otp/', views.VerifyOTP.as_view(), name='verify_otp'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/<int:pk>/', views.AdminUserProfileView.as_view(), name='user-profile-admin'),
    path('profile/list/', views.UserProfileView.as_view(), name='user_profile_list'),
    path('profile/edit/', views.UserProfileView.as_view(), name='user_profile_edit'),
]
    
