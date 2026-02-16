from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.asgi import application
from rooms.models import Room, RoomParticipant
from users.models import User
from .utils import wait_for_event


class ModerationTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password="pass",
            display_name="Host",
        )

        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass",
            display_name="User",
        )

        self.room = Room.objects.create(
            code="MOD001",
            host=self.host,
            video_provider="movie",
            video_id="x",
        )
        self.room.mark_live()

        RoomParticipant.objects.create(room=self.room, user=self.host)
        RoomParticipant.objects.create(room=self.room, user=self.user)

    async def _connect(self, user):
        token = AccessToken.for_user(user)
        communicator = WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    async def _drain_startup(self, communicator):
        for _ in range(3):
            await communicator.receive_json_from()

    async def test_mute_blocks_chat(self):
        host_comm = await self._connect(self.host)
        user_comm = await self._connect(self.user)

        await self._drain_startup(host_comm)
        await self._drain_startup(user_comm)

        # Host mutes user
        await host_comm.send_json_to({
            "type": "MUTE_USER",
            "user_id": str(self.user.id),
        })

        # Muted user tries to send message
        await user_comm.send_json_to({
            "type": "CHAT_MESSAGE",
            "message": "hello",
        })

        response = await wait_for_event(user_comm, "ERROR")
        self.assertIn("muted", response["message"].lower())

        await host_comm.disconnect()
        await user_comm.disconnect()

    async def test_ban_blocks_reconnect(self):
        host_comm = await self._connect(self.host)
        user_comm = await self._connect(self.user)

        await self._drain_startup(host_comm)
        await self._drain_startup(user_comm)

        # Host bans user
        await host_comm.send_json_to({
            "type": "BAN_USER",
            "user_id": str(self.user.id),
        })

        await user_comm.disconnect()

        # Try reconnecting
        token = AccessToken.for_user(self.user)
        new_comm = WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )
        connected, _ = await new_comm.connect()

        self.assertFalse(connected)

        await host_comm.disconnect()

    async def test_kick_disconnects_but_allows_reconnect(self):
        host_comm = await self._connect(self.host)
        user_comm = await self._connect(self.user)

        await self._drain_startup(host_comm)
        await self._drain_startup(user_comm)

        # Host kicks user
        await host_comm.send_json_to({
            "type": "KICK_USER",
            "user_id": str(self.user.id),
        })

        await user_comm.disconnect()

        # Reconnect should succeed
        token = AccessToken.for_user(self.user)
        new_comm = WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/?token={token}",
        )
        connected, _ = await new_comm.connect()

        self.assertTrue(connected)
        await new_comm.disconnect()
        await host_comm.disconnect()

    async def test_non_host_cannot_moderate(self):
        host_comm = await self._connect(self.host)
        user_comm = await self._connect(self.user)

        await self._drain_startup(host_comm)
        await self._drain_startup(user_comm)

        # Non-host tries to mute host
        await user_comm.send_json_to({
            "type": "MUTE_USER",
            "user_id": str(self.host.id),
        })

        # Host should still be able to chat
        await host_comm.send_json_to({
            "type": "CHAT_MESSAGE",
            "message": "still here",
        })

        response = await wait_for_event(host_comm, "CHAT_MESSAGE")

        await host_comm.disconnect()
        await user_comm.disconnect()
