from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken

from core.asgi import application
from rooms.models import Room, RoomParticipant
from users.models import User


class PlaybackVersioningTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        # ALL ORM here (sync safe)
        self.host = User.objects.create_user(
            email="host@test.com",
            password="pass",
            display_name="Host",
        )

        self.room = Room.objects.create(
            code="VER001",
            host=self.host,
            video_provider="x",
            video_id="y",
        )

        self.room.mark_live()

        RoomParticipant.objects.create(
            room=self.room,
            user=self.host,
            status=RoomParticipant.STATUS_APPROVED,
        )

    async def test_version_increments(self):
        token = AccessToken.for_user(self.host)

        comm = WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )

        connected, _ = await comm.connect()
        self.assertTrue(connected)

        # Drain initial messages (CHAT_HISTORY + ROOM_PARTICIPANTS + PLAYBACK_STATE)
        for _ in range(3):
            await comm.receive_json_from()

        # First update
        await comm.send_json_to({"type": "PLAY", "time": 10})
        event1 = await comm.receive_json_from()

        self.assertEqual(event1["type"], "PLAYBACK_STATE")
        self.assertEqual(event1["version"], 1)

        # Second update
        await comm.send_json_to({"type": "PAUSE", "time": 20})
        event2 = await comm.receive_json_from()

        self.assertEqual(event2["type"], "PLAYBACK_STATE")
        self.assertEqual(event2["version"], 2)

        await comm.disconnect()
