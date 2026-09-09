from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    login_view,
    logout_view,
    guest_login_view,
    guest_login,
    set_username,
    signup_view,
)

urlpatterns = [
    path("signup/", signup_view),
    path("login/", login_view),
    path("logout/", logout_view),
    path("guest/", guest_login_view),
    path("guest-login/", guest_login),
    path("set-username/", set_username),
    path("token/refresh/", TokenRefreshView.as_view()),
]
