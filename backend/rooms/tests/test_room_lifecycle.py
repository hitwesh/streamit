from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from rooms.models import Room
from users.models import User


class RoomLifecycleTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password="pass123",
            display_name="Host",
        )

        self.room = Room.objects.create(
            code="TEST01",
            host=self.host,
            video_provider="test",
            video_id="vid1",
        )

    # ---------- VALID TRANSITIONS ----------

    def test_created_to_live(self):
        self.assertEqual(self.room.state, Room.State.CREATED)

        self.room.mark_live()
        self.room.refresh_from_db()

        self.assertEqual(self.room.state, Room.State.LIVE)

    def test_live_to_grace(self):
        self.room.mark_live()
        self.room.mark_grace()
        self.room.refresh_from_db()

        self.assertEqual(self.room.state, Room.State.GRACE)

    def test_grace_to_expired(self):
        self.room.mark_live()
        self.room.mark_grace()

        self.room.mark_expired()
        self.room.refresh_from_db()

        self.assertEqual(self.room.state, Room.State.EXPIRED)

    def test_any_to_deleted(self):
        self.room.mark_deleted()
        self.room.refresh_from_db()

        self.assertEqual(self.room.state, Room.State.DELETED)
        self.assertFalse(self.room.is_active)

    # ---------- INVALID TRANSITIONS ----------

    def test_created_cannot_go_to_grace(self):
        self.room.mark_grace()
        self.room.refresh_from_db()

        self.assertEqual(self.room.state, Room.State.CREATED)

    def test_created_cannot_go_to_expired(self):
        self.room.mark_expired()
        self.room.refresh_from_db()

        self.assertEqual(self.room.state, Room.State.CREATED)

    def test_expired_cannot_go_live(self):
        self.room.mark_live()
        self.room.mark_grace()
        self.room.mark_expired()

        self.room.mark_live()
        self.room.refresh_from_db()

        self.assertEqual(self.room.state, Room.State.EXPIRED)

    def test_deleted_is_terminal(self):
        self.room.mark_deleted()

        self.room.mark_live()
        self.room.mark_grace()
        self.room.mark_expired()
        self.room.refresh_from_db()

        self.assertEqual(self.room.state, Room.State.DELETED)
