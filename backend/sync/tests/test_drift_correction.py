from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.asgi import application
from rooms.models import Room, RoomParticipant
from users.models import User
from .utils import wait_for_event


class DriftCorrectionTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password="pass",
            display_name="Host",
        )

        self.room = Room.objects.create(
            code="DRIFT01",
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

    async def test_sync_correction_when_drift_large(self):
        token = AccessToken.for_user(self.host)

        comm = WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )

        connected, _ = await comm.connect()
        self.assertTrue(connected)

        await wait_for_event(comm, "PLAYBACK_STATE")

        await comm.send_json_to({"type": "PLAY", "time": 100})
        await wait_for_event(comm, "PLAYBACK_STATE")

        await comm.send_json_to({
            "type": "SYNC_CHECK",
            "client_time": 90,
        })

        event = await wait_for_event(comm, "SYNC_CORRECTION")
        self.assertEqual(event["type"], "SYNC_CORRECTION")
        self.assertEqual(event["time"], 100)

        await comm.disconnect()
