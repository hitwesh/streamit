from django.contrib import admin
from .models import Room, RoomParticipant


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "host",
        "is_private",
        "entry_mode",
        "is_chat_enabled",
        "created_at",
    )
    search_fields = ("code",)
    list_filter = ("is_private", "entry_mode")


@admin.register(RoomParticipant)
class RoomParticipantAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "status", "joined_at")
    list_filter = ("status",)
