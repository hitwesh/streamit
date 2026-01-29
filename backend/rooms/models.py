from django.db import models

# Create your models here.
import uuid
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password, check_password

User = settings.AUTH_USER_MODEL


class Room(models.Model):
    ENTRY_APPROVAL = "APPROVAL"
    ENTRY_PASSWORD = "PASSWORD"

    ENTRY_MODES = [
        (ENTRY_APPROVAL, "Approval Required"),
        (ENTRY_PASSWORD, "Password Based"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)

    host = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="hosted_rooms"
    )

    is_private = models.BooleanField(default=False)
    entry_mode = models.CharField(
        max_length=10,
        choices=ENTRY_MODES,
        null=True,
        blank=True
    )

    entry_password_hash = models.CharField(
        max_length=128,
        null=True,
        blank=True
    )

    is_chat_enabled = models.BooleanField(default=True)

    video_provider = models.CharField(max_length=50)
    video_id = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def set_entry_password(self):
        """
        Auto-generate an 8-character password and store its hash.
        Returns the raw password ONCE (for display to host).
        """
        raw_password = get_random_string(length=8)
        self.entry_password_hash = make_password(raw_password)
        return raw_password

    def check_entry_password(self, raw_password):
        if not self.entry_password_hash:
            return False
        return check_password(raw_password, self.entry_password_hash)

    def __str__(self):
        return f"Room {self.code}"

class RoomParticipant(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
    ]

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="participants"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_APPROVED
    )

    joined_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("room", "user")

    def __str__(self):
        return f"{self.user} in {self.room}"
