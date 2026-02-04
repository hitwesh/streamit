import json
from django.utils import timezone

from common.redis_client import get_redis_client
from common.redis_keys import (
    room_state_key,
    room_host_status_key,
    room_participants_key,
)


# ======================
# Room lifecycle state
# ======================

async def room_connected(room_data: dict):
    client = get_redis_client()
    payload = {
        "is_active": room_data["is_active"],
        "updated_at": timezone.now().isoformat(),
    }
    await client.set(
        room_state_key(room_data["code"]),
        json.dumps(payload),
    )


async def room_disconnected(room_data: dict):
    client = get_redis_client()
    payload = {
        "is_active": room_data["is_active"],
        "updated_at": timezone.now().isoformat(),
    }
    await client.set(
        room_state_key(room_data["code"]),
        json.dumps(payload),
    )


# ======================
# Host presence
# ======================

async def host_connected(room_data: dict, user_id):
    if user_id != room_data["host_id"]:
        return

    client = get_redis_client()
    payload = {
        "status": "connected",
        "updated_at": timezone.now().isoformat(),
    }
    await client.set(
        room_host_status_key(room_data["code"]),
        json.dumps(payload),
    )


async def host_disconnected(room_data: dict, user_id):
    if user_id != room_data["host_id"]:
        return

    client = get_redis_client()
    payload = {
        "status": "disconnected",
        "updated_at": timezone.now().isoformat(),
    }
    await client.set(
        room_host_status_key(room_data["code"]),
        json.dumps(payload),
    )


# ======================
# Participants
# ======================

async def update_participants(room_code: str, participants: list[str]):
    client = get_redis_client()
    key = room_participants_key(room_code)

    await client.delete(key)
    if participants:
        await client.sadd(key, *participants)
