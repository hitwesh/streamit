import asyncio

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.core.management import call_command
from rest_framework_simplejwt.tokens import AccessToken

from core.asgi import application
from rooms.models import Room, RoomParticipant
from users.models import User
from .utils import wait_for_event


class GraceWithParticipantsTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.host = User.objects.create_user(
            email="host2@test.com",
            password="pass",
            display_name="Host",
        )

        self.viewer = User.objects.create_user(
            email="viewer2@test.com",
            password="pass",
            display_name="Viewer",
        )

        self.room = Room.objects.create(
            code="GRACE01",
            host=self.host,
            video_provider="x",
            video_id="y",
        )

        self.room.mark_live()

        RoomParticipant.objects.create(room=self.room, user=self.host)
        RoomParticipant.objects.create(room=self.room, user=self.viewer)

    async def _connect(self, user):
        token = AccessToken.for_user(user)
        return WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )

    async def test_participant_stays_during_grace_and_room_expires(self):
        host_ws = await self._connect(self.host)
        viewer_ws = await self._connect(self.viewer)

        await host_ws.connect()
        await viewer_ws.connect()

        await wait_for_event(viewer_ws, "ROOM_PARTICIPANTS")

        # Host disconnects -> grace starts
        await host_ws.disconnect()

        event = await wait_for_event(viewer_ws, "HOST_DISCONNECTED")
        self.assertIn("grace_seconds", event)

        # Wait beyond grace period
        await asyncio.sleep(Room.GRACE_PERIOD_SECONDS + 1)

        await database_sync_to_async(call_command)("expire_rooms")

        await database_sync_to_async(self.room.refresh_from_db)()
        state = await database_sync_to_async(lambda: self.room.state)()
        self.assertEqual(state, Room.State.EXPIRED)

        await viewer_ws.disconnect()
