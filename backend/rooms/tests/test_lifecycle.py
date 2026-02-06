from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from rooms.models import Room
from rooms.services import create_room
from users.models import User


class RoomLifecycleTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password="password",
            display_name="Host",
        )

        self.room, _ = create_room(
            host=self.host,
            is_private=False,
            entry_mode=None,
        )

    def test_room_starts_created(self):
        self.assertEqual(self.room.state, Room.State.CREATED)

    def test_mark_live(self):
        self.room.mark_live()
        self.room.refresh_from_db()
        self.assertEqual(self.room.state, Room.State.LIVE)

    def test_mark_grace(self):
        self.room.mark_live()
        self.room.mark_grace()
        self.room.refresh_from_db()
        self.assertEqual(self.room.state, Room.State.GRACE)

    def test_grace_expiry_marks_expired(self):
        self.room.mark_live()
        self.room.host_disconnected_at = timezone.now() - timedelta(
            seconds=Room.GRACE_PERIOD_SECONDS + 1
        )
        self.room.mark_grace()
        self.room.save()

        call_command("expire_rooms")

        self.room.refresh_from_db()
        self.assertEqual(self.room.state, Room.State.EXPIRED)
