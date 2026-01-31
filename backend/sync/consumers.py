import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from rooms.models import Room, RoomParticipant


class RoomPresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        self.user = self.scope["user"]

        # 1️⃣ Auth check
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # 2️⃣ Room existence
        self.room = await self.get_room()
        room = self.room
        if not room:
            await self.close(code=4002)
            return

        # 3️⃣ Participant approval
        is_allowed = await self.is_approved_participant(room)
        if not is_allowed:
            await self.close(code=4003)
            return

        # 4️⃣ Join room group
        self.room_group_name = f"room_{room.code}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        # 5️⃣ Notify presence
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user": self.user.display_name,
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_left",
                    "user": self.user.display_name,
                }
            )

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        event_type = data.get("type")
        if not event_type:
            return

    # ---------------- CHAT ----------------
        if event_type == "CHAT_MESSAGE":
            if not self.room.is_chat_enabled:
                await self.send(text_data=json.dumps({
                    "type": "ERROR",
                    "error": "Chat is disabled",
                }))
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "room_event",
                    "event": {
                        "type": "CHAT_MESSAGE",
                        "user": self.user.display_name,
                        "message": data.get("message", ""),
                    },
                }
            )
            return

        # ---------------- PLAYBACK (HOST ONLY) ----------------
        if event_type in {"PLAY", "PAUSE", "SEEK"}:
            if self.user.id != self.room.host_id:
                return  # silently ignore

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "room_event",
                    "event": {
                        "type": event_type,
                        "time": data.get("time"),
                    },
                }
            )
            return

        # Playback events → host only
        if event_type in {"PLAY", "PAUSE", "SEEK"}:
            if self.user.id != self.room.host_id:
                # Not host → ignore
                return
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "room_event",
                    "event": data,
                }
            )

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            "type": "USER_JOINED",
            "user": event["user"],
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            "type": "USER_LEFT",
            "user": event["user"],
        }))

    async def room_event(self, event):
        """
        Send room events to WebSocket
        """
        await self.send(text_data=json.dumps(event["event"]))

    # ---------- DB helpers ----------

    @database_sync_to_async
    def get_room(self):
        try:
            return Room.objects.get(code=self.room_code)
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def is_approved_participant(self, room):
        return RoomParticipant.objects.filter(
            room=room,
            user=self.user,
            status=RoomParticipant.STATUS_APPROVED,
        ).exists()
