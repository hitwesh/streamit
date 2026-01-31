from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "created_at")
    search_fields = ("message",)
