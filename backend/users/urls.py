from django.urls import path
from .views import login_view, logout_view, guest_login_view, guest_login, set_username

urlpatterns = [
    path("login/", login_view),
    path("logout/", logout_view),
    path("guest/", guest_login_view),
    path("guest-login/", guest_login),
    path("set-username/", set_username),
]
