from django.urls import path
from .views import login_view, logout_view, guest_login_view

urlpatterns = [
    path("login/", login_view),
    path("logout/", logout_view),
    path("guest/", guest_login_view),
]
