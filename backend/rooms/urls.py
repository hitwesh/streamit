from django.urls import path
from .views import (
    create_room_view,
    join_room_view,
    approve_participant_view,
)

urlpatterns = [
    path("create/", create_room_view),
    path("join/", join_room_view),
    path("approve/", approve_participant_view),
]
