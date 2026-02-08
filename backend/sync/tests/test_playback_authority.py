from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.asgi import application
from rooms.models import Room, RoomParticipant
from users.models import User
from .utils import wait_for_event


class PlaybackAuthorityTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password="pass",
            display_name="Host",
        )

        self.viewer = User.objects.create_user(
            email="viewer@test.com",
            password="pass",
            display_name="Viewer",
        )

        self.room = Room.objects.create(
            code="AUTH01",
            host=self.host,
            video_provider="x",
            video_id="y",
        )

        RoomParticipant.objects.create(room=self.room, user=self.host)
        RoomParticipant.objects.create(room=self.room, user=self.viewer)

    async def _connect(self, user):
        token = AccessToken.for_user(user)
        return WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )

    async def test_non_host_cannot_control_playback(self):
        comm = await self._connect(self.viewer)
        connected, _ = await comm.connect()
        self.assertTrue(connected)

        await wait_for_event(comm, "PLAYBACK_STATE")

        await comm.send_json_to({"type": "PLAY", "time": 100})

        # Viewer should NOT receive their own playback event
        with self.assertRaises(AssertionError):
            await wait_for_event(comm, "PLAY", timeout=0.3)

    async def test_host_can_control_playback(self):
        comm = await self._connect(self.host)
        connected, _ = await comm.connect()
        self.assertTrue(connected)

        await wait_for_event(comm, "PLAYBACK_STATE")

        await comm.send_json_to({"type": "PLAY", "time": 50})
        event = await wait_for_event(comm, "PLAY")

        self.assertEqual(event["type"], "PLAY")
        self.assertEqual(event["time"], 50)
