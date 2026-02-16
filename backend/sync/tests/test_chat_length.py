from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.asgi import application
from rooms.models import Room, RoomParticipant
from users.models import User


class ChatLengthTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(
            email="len@test.com",
            password="pass",
            display_name="LenUser",
        )

        self.room = Room.objects.create(
            code="LEN001",
            host=self.user,
            video_provider="x",
            video_id="y",
        )
        self.room.mark_live()

        RoomParticipant.objects.create(room=self.room, user=self.user)

    async def test_message_too_long(self):
        token = AccessToken.for_user(self.user)
        comm = WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )

        connected, _ = await comm.connect()
        self.assertTrue(connected)

        for _ in range(3):
            await comm.receive_json_from()

        long_message = "a" * 600

        await comm.send_json_to({
            "type": "CHAT_MESSAGE",
            "message": long_message,
        })

        event = await comm.receive_json_from()
        self.assertEqual(event["type"], "ERROR")

        await comm.disconnect()
