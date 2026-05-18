from django.urls import path
from .views import (
    create_room_view,
    join_room_view,
    approve_participant_view,
    delete_room_view,
    room_detail_view,
    room_participants_view,
    room_source_view,
    public_rooms_view,
    search_content,
    save_progress_view,
    get_progress_view,
    resume_progress_view,
)

urlpatterns = [
    path("create/", create_room_view),
    path("join/", join_room_view),
    path("approve/", approve_participant_view),
    path("delete/", delete_room_view),
    path("participants/", room_participants_view),
    path("source/", room_source_view),
    path("progress/save/", save_progress_view),
    path("progress/get/", get_progress_view),
    path("<str:room_code>/detail/", room_detail_view),
    path("<str:room_code>/resume/", resume_progress_view),
    path("public/", public_rooms_view),
    path("search/", search_content),
]
