from django.urls import path
from .views import create_room_view

urlpatterns = [
    path("create/", create_room_view),
]
