from django.urls import path
from .views import (
    create_room_view,
    join_room_view,
    approve_participant_view,
    delete_room_view,
    public_rooms_view,
)

urlpatterns = [
    path("create/", create_room_view),
    path("join/", join_room_view),
    path("approve/", approve_participant_view),
    path("delete/", delete_room_view),
    path("public/", public_rooms_view),
]
