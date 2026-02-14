from django.db import models

# Create your models here.
import uuid
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta

User = settings.AUTH_USER_MODEL


class Room(models.Model):
    ENTRY_APPROVAL = "APPROVAL"
    ENTRY_PASSWORD = "PASSWORD"

    ENTRY_MODES = [
        (ENTRY_APPROVAL, "Approval Required"),
        (ENTRY_PASSWORD, "Password Based"),
    ]

    class State(models.TextChoices):
        CREATED = "CREATED"
        LIVE = "LIVE"
        GRACE = "GRACE"
        EXPIRED = "EXPIRED"
        DELETED = "DELETED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True)

    state = models.CharField(
        max_length=16,
        choices=State.choices,
        default=State.CREATED,
        db_index=True,
    )

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

    # NEW
    host_disconnected_at = models.DateTimeField(null=True, blank=True)

    GRACE_PERIOD_SECONDS = 30  # 30 seconds for testing

    def is_in_grace(self):
        if not self.host_disconnected_at:
            return False
        return timezone.now() < self.host_disconnected_at + timedelta(seconds=self.GRACE_PERIOD_SECONDS)

    def grace_expired(self):
        if not self.host_disconnected_at:
            return False
        return timezone.now() >= self.host_disconnected_at + timedelta(seconds=self.GRACE_PERIOD_SECONDS)

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

    def _can_transition(self, target):
        terminal = {self.State.EXPIRED, self.State.DELETED}

        if self.state in terminal:
            return False

        allowed = {
            self.State.CREATED: {self.State.LIVE},
            self.State.LIVE: {self.State.GRACE},
            self.State.GRACE: {self.State.LIVE, self.State.EXPIRED},
        }

        return target in allowed.get(self.state, set())

    def mark_live(self):
        if self._can_transition(self.State.LIVE):
            self.state = self.State.LIVE
            self.save(update_fields=["state"])

    def mark_grace(self):
        if self._can_transition(self.State.GRACE):
            self.state = self.State.GRACE
            self.save(update_fields=["state"])

    def mark_expired(self):
        if self._can_transition(self.State.EXPIRED):
            self.state = self.State.EXPIRED
            self.is_active = False
            self.save(update_fields=["state", "is_active"])

    def mark_deleted(self):
        self.state = self.State.DELETED
        self.is_active = False
        self.save(update_fields=["state", "is_active"])

    def __str__(self):
        return f"Room {self.code}"


class RoomPlaybackState(models.Model):
    room = models.OneToOneField(
        Room,
        on_delete=models.CASCADE,
        related_name="playback_state"
    )
    is_playing = models.BooleanField(default=False)
    current_time = models.FloatField(default=0.0)
    version = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

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


class WatchProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watch_progress"
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="watch_progress"
    )

    media_id = models.CharField(max_length=255)
    media_type = models.CharField(max_length=20)  # movie / tv

    season = models.IntegerField(null=True, blank=True)
    episode = models.IntegerField(null=True, blank=True)

    timestamp = models.FloatField(default=0.0)
    duration = models.FloatField(default=0.0)
    progress_percent = models.FloatField(default=0.0)
    completed = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "room", "media_id", "season", "episode")

    def __str__(self):
        return f"{self.user} - {self.media_id}"
