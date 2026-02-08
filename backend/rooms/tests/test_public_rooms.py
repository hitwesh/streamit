from asgiref.sync import async_to_sync
from django.test import TestCase

from common.redis_room_state import update_participants
from rooms.models import Room
from users.models import User


class PublicRoomsTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password="pass",
            display_name="Host",
        )

        self.room = Room.objects.create(
            code="PUB123",
            host=self.host,
            is_private=False,
            video_provider="x",
            video_id="y",
        )
        self.room.mark_live()

        async_to_sync(update_participants)(
            self.room.code,
            ["Host", "Alice", "Bob"],
        )

    def test_public_room_listed(self):
        res = self.client.get("/api/rooms/public/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["viewers"], 3)

    def test_private_room_hidden(self):
        self.room.is_private = True
        self.room.save()

        res = self.client.get("/api/rooms/public/")
        self.assertEqual(res.json(), [])
