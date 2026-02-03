# ===== Imports =====

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


# ===== Constants (event types, close codes if any) =====


# ===== DB ACCESS HELPERS (SYNC ONLY) =====
# All functions here:
# - touch ORM
# - fully resolve data
# - return primitives / dicts only

@database_sync_to_async
def get_room(room_code):
    try:
        return Room.objects.get(code=room_code)
    except Room.DoesNotExist:
        return None


@database_sync_to_async
def is_approved_participant(room, user):
    return RoomParticipant.objects.filter(
        room=room,
        user=user,
        status=RoomParticipant.STATUS_APPROVED,
    ).exists()


@database_sync_to_async
def save_message(room, user, text):
    ChatMessage.objects.create(
        room=room,
        user=user,
        message=text,
    )


@database_sync_to_async
def get_recent_messages(room, limit=50):
    return list(
        ChatMessage.objects
        .filter(room=room)
        .select_related("user")
        .order_by("-created_at")[:limit]
    )[::-1]


@database_sync_to_async
def get_playback_state(room):
    from rooms.models import RoomPlaybackState
    state, _ = RoomPlaybackState.objects.get_or_create(room=room)
    return state


@database_sync_to_async
def update_playback_state(room, is_playing, time):
    from rooms.models import RoomPlaybackState
    state, _ = RoomPlaybackState.objects.get_or_create(room=room)
    state.is_playing = is_playing
    state.current_time = time
    state.save()


@database_sync_to_async
def mark_host_disconnected(room):
    room.host_disconnected_at = timezone.now()
    room.save(update_fields=["host_disconnected_at"])


@database_sync_to_async
def clear_grace(room):
    room.host_disconnected_at = None
    room.save(update_fields=["host_disconnected_at"])


@database_sync_to_async
def get_participant_payload(room):
    participants = list(
        RoomParticipant.objects
        .filter(room=room, status=RoomParticipant.STATUS_APPROVED)
        .select_related("user")
        .values_list("user__display_name", flat=True)
    )

    host_name = (
        Room.objects
        .select_related("host")
        .get(id=room.id)
        .host
        .display_name
    )

    return {
        "participants": participants,
        "host": host_name,
    }


# ===== REDIS HELPERS =====
# All Redis reads/writes
# No DB access here

async def cache_room_state(room):
    client = get_redis_client()
    payload = {
        "is_active": room.is_active,
        "updated_at": timezone.now().isoformat(),
    }
    await client.set(room_state_key(room.code), json.dumps(payload))


async def cache_host_status(user, room, status):
    if user.id != room.host_id:
        return
    client = get_redis_client()
    payload = {
        "status": status,
        "updated_at": timezone.now().isoformat(),
    }
    await client.set(room_host_status_key(room.code), json.dumps(payload))


async def cache_participants(room_code, participants):
    client = get_redis_client()
    key = room_participants_key(room_code)
    if participants:
        await client.delete(key)
        await client.sadd(key, *participants)
    else:
        await client.delete(key)


# ===== AUTHORITY & VALIDATION HELPERS =====
# is_host?
# is_chat_enabled?
# validation rules


# ===== CONSUMER CLASS =====
class RoomPresenceConsumer(AsyncWebsocketConsumer):
    # --- Connection lifecycle ---
    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        self.user = self.scope["user"]

        # 1️⃣ Auth check
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # 2️⃣ Room existence
        self.room = await get_room(self.room_code)
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
            await clear_grace(room)

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "host_reconnected"}
            )

        # 3️⃣ Participant approval
        is_allowed = await is_approved_participant(room, self.user)
        if not is_allowed:
            await self.close(code=4003)
            return

        # 4️⃣ Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        await cache_room_state(room)
        await cache_host_status(self.user, room, "connected")

        await self.broadcast_participants()

        messages = await get_recent_messages(room)

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

        state = await get_playback_state(room)

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
                await mark_host_disconnected(self.room)

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
            await cache_room_state(self.room)
            await cache_host_status(self.user, self.room, "disconnected")

    # --- Incoming message router ---
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

            await save_message(self.room, self.user, message_text)

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

            await update_playback_state(self.room, is_playing, time)

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

    # --- Event handlers ---
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
        payload = await get_participant_payload(self.room)

        await cache_participants(self.room.code, payload["participants"])

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "room_participants",
                "participants": payload["participants"],
                "host": payload["host"],
            }
        )

    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            "type": "ERROR",
            "message": message,
        }))
