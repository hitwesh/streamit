from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.asgi import application
from rooms.models import Room, RoomParticipant, WatchProgress
from users.models import User


class ProgressCompletionTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password="pass",
            display_name="Host",
        )

        self.room = Room.objects.create(
            code="END001",
            host=self.host,
            video_provider="movie",
            video_id="y",
        )
        self.room.mark_live()

        RoomParticipant.objects.create(room=self.room, user=self.host)

    async def _connect(self, user):
        token = AccessToken.for_user(user)
        return WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )

    async def test_video_ended_sets_100_percent(self):
        communicator = await self._connect(self.host)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to({
            "type": "PLAYER_EVENT",
            "data": {
                "event": "ended",
                "currentTime": 7200,
                "duration": 7200,
                "progress": 100,
            },
        })

        await communicator.disconnect()

        progress = await database_sync_to_async(WatchProgress.objects.get)(
            user=self.host,
            room=self.room,
        )
        self.assertEqual(progress.progress_percent, 100.0)
        self.assertTrue(progress.completed)
