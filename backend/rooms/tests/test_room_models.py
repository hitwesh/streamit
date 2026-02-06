import os

from django.test import TestCase

from rooms.models import Room
from users.models import User


TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "test-password")


class RoomModelTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password=TEST_PASSWORD,
            display_name="Host",
        )
        self.room = Room.objects.create(
            code="ABC123",
            host=self.host,
            video_provider="",
            video_id="",
        )

    def test_room_initial_state(self):
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

    def test_mark_expired(self):
        self.room.mark_live()
        self.room.mark_grace()
        self.room.mark_expired()
        self.room.refresh_from_db()
        self.assertEqual(self.room.state, Room.State.EXPIRED)
