"""
URLs for accounts app.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, UserProfileView,
    my_invite_tokens, generate_invite_tokens, referral_chain, delete_invite_token,
    check_email_availability, check_username_availability, check_invite_token,
    verify_email, resend_verification_email,
    password_reset_request, password_reset_confirm
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('invite/my/', my_invite_tokens, name='my_invite_tokens'),
    path('invite/generate/', generate_invite_tokens, name='generate_invite_tokens'),
    path('invite/<int:token_id>/delete/', delete_invite_token, name='delete_invite_token'),
    path('referral-chain/', referral_chain, name='referral_chain'),
    path('check/email/', check_email_availability, name='check_email'),
    path('check/username/', check_username_availability, name='check_username'),
    path('check/invite-token/', check_invite_token, name='check_invite_token'),
    path('verify-email/', verify_email, name='verify_email'),
    path('resend-verification/', resend_verification_email, name='resend_verification'),
    path('password-reset-request/', password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/', password_reset_confirm, name='password_reset_confirm'),
]

