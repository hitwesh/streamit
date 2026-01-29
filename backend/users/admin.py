from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("display_name", "email", "is_guest", "is_staff")
    search_fields = ("email", "display_name")
