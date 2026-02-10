from asgiref.sync import async_to_sync
from django.test import TestCase

from common.redis_client import get_redis_client
from common.redis_keys import room_host_status_key, room_viewers_key
from common.redis_room_state import host_connected, increment_viewers
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

        async_to_sync(self._clear_redis_keys)(self.room.code)

        room_data = {
            "code": self.room.code,
            "host_id": self.host.id,
            "is_active": True,
        }
        async_to_sync(host_connected)(room_data, self.host.id)
        async_to_sync(increment_viewers)(self.room.code)
        async_to_sync(increment_viewers)(self.room.code)
        async_to_sync(increment_viewers)(self.room.code)

    def tearDown(self):
        async_to_sync(self._clear_redis_keys)(self.room.code)

    async def _clear_redis_keys(self, room_code):
        client = get_redis_client()
        await client.delete(room_host_status_key(room_code))
        await client.delete(room_viewers_key(room_code))

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
