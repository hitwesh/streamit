import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from chat.models import ChatMessage

from rooms.models import Room, RoomParticipant
from common.redis_client import get_redis_client
from common.redis_keys import (
    room_host_status_key,
    room_participants_key,
    room_state_key,
)


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

        if not room.is_active:
            await self.close(code=4005)
            return

        if room.grace_expired():
            await self.close(code=4004)
            return

        self.room_group_name = f"room_{room.code}"

        if self.user.id == room.host_id and room.is_in_grace():
            await self.clear_grace()

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "host_reconnected"}
            )

        # 3️⃣ Participant approval
        is_allowed = await self.is_approved_participant(room)
        if not is_allowed:
            await self.close(code=4003)
            return

        # 4️⃣ Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        await self.cache_room_state()
        await self.cache_host_status("connected")

        await self.broadcast_participants()

        messages = await self.get_recent_messages()

        await self.send(text_data=json.dumps({
            "type": "CHAT_HISTORY",
            "messages": [
                {
                    "user": m.user.display_name,
                    "message": m.message,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ]
        }))

        state = await self.get_playback_state()

        await self.send(text_data=json.dumps({
            "type": "PLAYBACK_STATE",
            "is_playing": state.is_playing,
            "time": state.current_time,
        }))

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
            if self.user.id == self.room.host_id:
                await self.mark_host_disconnected()

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "host_disconnected",
                        "grace_seconds": Room.GRACE_PERIOD_SECONDS,
                    }
                )
            else:
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

        if hasattr(self, "room"):
            await self.cache_room_state()
            await self.cache_host_status("disconnected")

    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            "type": "ERROR",
            "message": message,
        }))

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
                await self.send_error("Chat is disabled in this room")
                return

            message_text = data.get("message", "").strip()
            if not message_text:
                return

            await self.save_message(message_text)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "room_event",
                    "event": {
                        "type": "CHAT_MESSAGE",
                        "user": self.user.display_name,
                        "message": message_text,
                    },
                }
            )
            return

        # ---------------- PLAYBACK (HOST ONLY) ----------------
        if event_type in {"PLAY", "PAUSE", "SEEK"}:
            if self.user.id != self.room.host_id:
                return  # silently ignore

            is_playing = event_type == "PLAY"
            time = data.get("time", 0)

            await self.update_playback_state(is_playing, time)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "room_event",
                    "event": {
                        "type": event_type,
                        "time": time,
                    },
                }
            )
            return

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

    async def host_disconnected(self, event):
        await self.send(text_data=json.dumps({
            "type": "HOST_DISCONNECTED",
            "grace_seconds": event["grace_seconds"],
        }))

    async def host_reconnected(self, event):
        await self.send(text_data=json.dumps({
            "type": "HOST_RECONNECTED"
        }))

    async def room_deleted(self, event):
        await self.send(text_data=json.dumps({
            "type": "ROOM_DELETED"
        }))
        await self.close()

    async def room_event(self, event):
        """
        Send room events to WebSocket
        """
        await self.send(text_data=json.dumps(event["event"]))

    async def room_participants(self, event):
        await self.send(text_data=json.dumps({
            "type": "ROOM_PARTICIPANTS",
            "participants": event["participants"],
            "host": event["host"],
        }))

    async def broadcast_participants(self):
        payload = await self.get_participant_payload()

        await self.cache_participants(payload["participants"])

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "room_participants",
                "participants": payload["participants"],
                "host": payload["host"],
            }
        )

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

    @database_sync_to_async
    def save_message(self, text):
        ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            message=text,
        )

    @database_sync_to_async
    def get_recent_messages(self, limit=50):
        return list(
            ChatMessage.objects
            .filter(room=self.room)
            .select_related("user")
            .order_by("-created_at")[:limit]
        )[::-1]

    @database_sync_to_async
    def get_playback_state(self):
        from rooms.models import RoomPlaybackState
        state, _ = RoomPlaybackState.objects.get_or_create(room=self.room)
        return state

    @database_sync_to_async
    def update_playback_state(self, is_playing, time):
        from rooms.models import RoomPlaybackState
        state, _ = RoomPlaybackState.objects.get_or_create(room=self.room)
        state.is_playing = is_playing
        state.current_time = time
        state.save()

    @database_sync_to_async
    def mark_host_disconnected(self):
        self.room.host_disconnected_at = timezone.now()
        self.room.save(update_fields=["host_disconnected_at"])

    @database_sync_to_async
    def clear_grace(self):
        self.room.host_disconnected_at = None
        self.room.save(update_fields=["host_disconnected_at"])

    @database_sync_to_async
    def get_participant_payload(self):
        participants = list(
            RoomParticipant.objects
            .filter(room=self.room, status=RoomParticipant.STATUS_APPROVED)
            .select_related("user")
            .values_list("user__display_name", flat=True)
        )

        host_name = (
            Room.objects
            .select_related("host")
            .get(id=self.room.id)
            .host
            .display_name
        )

        return {
            "participants": participants,
            "host": host_name,
        }

    async def cache_room_state(self):
        client = get_redis_client()
        payload = {
            "is_active": self.room.is_active,
            "updated_at": timezone.now().isoformat(),
        }
        await client.set(room_state_key(self.room.code), json.dumps(payload))

    async def cache_host_status(self, status):
        if self.user.id != self.room.host_id:
            return
        client = get_redis_client()
        payload = {
            "status": status,
            "updated_at": timezone.now().isoformat(),
        }
        await client.set(room_host_status_key(self.room.code), json.dumps(payload))

    async def cache_participants(self, participants):
        client = get_redis_client()
        key = room_participants_key(self.room.code)
        if participants:
            await client.delete(key)
            await client.sadd(key, *participants)
        else:
            await client.delete(key)
