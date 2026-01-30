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
        room = await self.get_room()
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
