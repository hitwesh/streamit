# ===== Imports =====

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from chat.models import ChatMessage

from rooms.models import Room, RoomParticipant
from common.redis_room_state import (
    room_connected,
    room_disconnected,
    host_connected,
    host_disconnected,
    update_participants,
)


# ===== Constants (event types, close codes if any) =====


# ===== DB ACCESS HELPERS (SYNC ONLY) =====
# All functions here:
# - touch ORM
# - fully resolve data
# - return primitives / dicts only

@database_sync_to_async
def get_room_snapshot(room_code):
    try:
        room = Room.objects.get(code=room_code)
        return {
            "id": room.id,
            "code": room.code,
            "host_id": room.host_id,
            "is_active": room.is_active,
            "is_chat_enabled": room.is_chat_enabled,
            "host_disconnected_at": room.host_disconnected_at,
        }
    except Room.DoesNotExist:
        return None


@database_sync_to_async
def is_approved_participant(room_id, user):
    return RoomParticipant.objects.filter(
        room_id=room_id,
        user=user,
        status=RoomParticipant.STATUS_APPROVED,
    ).exists()


@database_sync_to_async
def save_message_by_room_id(room_id, user, text):
    ChatMessage.objects.create(
        room_id=room_id,
        user=user,
        message=text,
    )


@database_sync_to_async
def get_recent_messages_by_room_id(room_id, limit=50):
    messages = (
        ChatMessage.objects
        .filter(room_id=room_id)
        .select_related("user")
        .order_by("-created_at")[:limit]
    )

    return [
        {
            "user": m.user.display_name,
            "message": m.message,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(list(messages))
    ]


@database_sync_to_async
def get_playback_state_by_room_id(room_id):
    from rooms.models import RoomPlaybackState
    state, _ = RoomPlaybackState.objects.get_or_create(room_id=room_id)
    return {
        "is_playing": state.is_playing,
        "time": state.current_time,
    }


@database_sync_to_async
def update_playback_state_by_room_id(room_id, is_playing, time):
    from rooms.models import RoomPlaybackState
    state, _ = RoomPlaybackState.objects.get_or_create(room_id=room_id)
    state.is_playing = is_playing
    state.current_time = time
    state.save()


@database_sync_to_async
def mark_host_disconnected_by_room_id(room_id):
    Room.objects.filter(id=room_id).update(
        host_disconnected_at=timezone.now()
    )


@database_sync_to_async
def clear_grace_by_room_id(room_id):
    Room.objects.filter(id=room_id).update(host_disconnected_at=None)


@database_sync_to_async
def get_participant_payload_by_room_id(room_id):
    qs = (
        RoomParticipant.objects
        .filter(room_id=room_id, status=RoomParticipant.STATUS_APPROVED)
        .select_related("user", "room__host")
    )

    participants = []
    host_name = None

    for rp in qs:
        participants.append(rp.user.display_name)
        if rp.user_id == rp.room.host_id:
            host_name = rp.user.display_name

    return {
        "participants": participants,
        "host": host_name,
    }


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
        self.room_data = await get_room_snapshot(self.room_code)
        room = self.room_data
        if not room:
            await self.close(code=4002)
            return

        if not room["is_active"]:
            await self.close(code=4005)
            return

        if room["host_disconnected_at"] and timezone.now() - room["host_disconnected_at"] > timezone.timedelta(
            seconds=Room.GRACE_PERIOD_SECONDS
        ):
            await self.close(code=4004)
            return

        self.room_group_name = f"room_{room['code']}"

        if self.user.id == room["host_id"] and room["host_disconnected_at"] and timezone.now() - room["host_disconnected_at"] <= timezone.timedelta(
            seconds=Room.GRACE_PERIOD_SECONDS
        ):
            await clear_grace_by_room_id(room["id"])

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "host_reconnected"}
            )

        # 3️⃣ Participant approval
        is_allowed = await is_approved_participant(room["id"], self.user)
        if not is_allowed:
            await self.close(code=4003)
            return

        # 4️⃣ Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        await room_connected(room)
        await host_connected(room, self.user.id)

        await self.broadcast_participants()

        messages = await get_recent_messages_by_room_id(room["id"])

        await self.send(text_data=json.dumps({
            "type": "CHAT_HISTORY",
            "messages": messages,
        }))

        state = await get_playback_state_by_room_id(room["id"])

        await self.send(text_data=json.dumps({
            "type": "PLAYBACK_STATE",
            "is_playing": state["is_playing"],
            "time": state["time"],
        }))

        # 5️⃣ Notify presence
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user": self.user.display_name,
                "exclude_channel": self.channel_name,
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            if self.user.id == self.room_data["host_id"]:
                await mark_host_disconnected_by_room_id(self.room_data["id"])

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

        if hasattr(self, "room_data"):
            await room_disconnected(self.room_data)
            await host_disconnected(self.room_data, self.user.id)

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
            if not self.room_data["is_chat_enabled"]:
                await self.send_error("Chat is disabled in this room")
                return

            message_text = data.get("message", "").strip()
            if not message_text:
                return

            await save_message_by_room_id(self.room_data["id"], self.user, message_text)

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
            if self.user.id != self.room_data["host_id"]:
                return  # silently ignore

            is_playing = event_type == "PLAY"
            time = data.get("time", 0)

            await update_playback_state_by_room_id(self.room_data["id"], is_playing, time)

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
        if event.get("exclude_channel") == self.channel_name:
            return

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
        payload = await get_participant_payload_by_room_id(self.room_data["id"])

        await update_participants(self.room_data["code"], payload["participants"])

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
