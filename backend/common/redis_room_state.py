import json
from django.utils import timezone

from common.redis_client import get_redis_client
from common.redis_keys import (
    room_state_key,
    room_host_status_key,
    room_participants_key,
    room_viewers_key,
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


async def get_viewer_count(room_code: str) -> int:
    client = get_redis_client()
    viewers = await client.get(room_viewers_key(room_code))
    return int(viewers or 0)


async def increment_viewers(room_code: str):
    client = get_redis_client()
    await client.incr(room_viewers_key(room_code))


async def decrement_viewers(room_code: str):
    client = get_redis_client()
    value = await client.decr(room_viewers_key(room_code))
    if value <= 0:
        await client.delete(room_viewers_key(room_code))


# ======================
# Grace period (TTL)
# ======================

async def start_grace(room_code: str, ttl_seconds: int):
    client = get_redis_client()
    await client.set(
        f"room:{room_code}:grace",
        "1",
        ex=ttl_seconds,
    )


async def clear_grace(room_code: str):
    client = get_redis_client()
    await client.delete(f"room:{room_code}:grace")


async def is_in_grace(room_code: str) -> bool:
    client = get_redis_client()
    return await client.exists(f"room:{room_code}:grace") == 1
