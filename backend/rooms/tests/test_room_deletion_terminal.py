from django.test import TestCase

from rooms.models import Room
from users.models import User


class RoomDeletionTerminalTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email="host3@test.com",
            password="pass",
            display_name="Host",
        )

        self.room = Room.objects.create(
            code="DEL01",
            host=self.host,
            video_provider="x",
            video_id="y",
        )

    def test_deleted_room_cannot_transition(self):
        self.room.mark_live()
        self.room.mark_grace()
        self.room.mark_deleted()

        self.room.mark_live()
        self.room.mark_grace()

        self.room.refresh_from_db()
        self.assertEqual(self.room.state, Room.State.DELETED)
