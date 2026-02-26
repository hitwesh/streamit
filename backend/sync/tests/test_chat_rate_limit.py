import os

from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.asgi import application
from rooms.models import Room, RoomParticipant
from users.models import User
from .utils import wait_for_event


TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "test-password")


class ChatRateLimitTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password=TEST_PASSWORD,
            display_name="User",
        )

        self.room = Room.objects.create(
            code="RATE01",
            host=self.user,
            video_provider="x",
            video_id="y",
        )
        self.room.mark_live()

        RoomParticipant.objects.create(
            room=self.room,
            user=self.user,
        )

    async def _connect(self):
        token = AccessToken.for_user(self.user)
        return WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )

    async def test_rate_limit_and_cooldown(self):
        comm = await self._connect()
        connected, _ = await comm.connect()
        self.assertTrue(connected)

        for _ in range(3):
            await comm.receive_json_from()

        for index in range(5):
            await comm.send_json_to({
                "type": "CHAT_MESSAGE",
                "message": f"spam-{index}",
            })
            await comm.receive_json_from()

        await comm.send_json_to({
            "type": "CHAT_MESSAGE",
            "message": "spam-5",
        })

        event = await wait_for_event(comm, "ERROR")
        self.assertIn("Rate limit", event["message"])

        await comm.send_json_to({
            "type": "CHAT_MESSAGE",
            "message": "spam2",
        })

        event2 = await wait_for_event(comm, "ERROR")
        self.assertIn("Rate limit", event2["message"])

        await comm.disconnect()
