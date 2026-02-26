import json
import time
from django.utils import timezone

from common.redis_client import get_redis_client
from common.redis_keys import (
    room_state_key,
    room_host_status_key,
    room_participants_key,
    room_viewers_key,
    chat_rate_window_key,
    chat_cooldown_key,
    chat_duplicate_key,
    room_muted_users_key,
    room_banned_users_key,
)

RATE_LIMIT_COUNT = 5
RATE_LIMIT_WINDOW = 3  # seconds
COOLDOWN_SECONDS = 10
DUPLICATE_WINDOW_SECONDS = 3


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


async def is_chat_blocked(room_code: str, user_id: str) -> bool:
    """
    Returns True if user is currently in cooldown.
    """
    client = get_redis_client()
    return await client.exists(
        chat_cooldown_key(room_code, str(user_id))
    )


async def check_and_update_rate_limit(room_code: str, user_id: str) -> bool:
    """
    Returns True if message should be blocked.
    """

    client = get_redis_client()

    if await is_chat_blocked(room_code, user_id):
        return True

    key = chat_rate_window_key(room_code, str(user_id))
    now = time.time()

    await client.zadd(key, {str(now): now})

    await client.zremrangebyscore(
        key,
        0,
        now - RATE_LIMIT_WINDOW,
    )

    count = await client.zcard(key)

    if count > RATE_LIMIT_COUNT:
        await client.set(
            chat_cooldown_key(room_code, str(user_id)),
            "1",
            ex=COOLDOWN_SECONDS,
        )
        await client.delete(key)
        return True

    await client.expire(key, RATE_LIMIT_WINDOW)
    return False


async def is_duplicate_message(room_code: str, user_id: str, message: str) -> bool:
    """
    Prevent sending identical messages repeatedly within short window.
    """
    client = get_redis_client()
    key = chat_duplicate_key(room_code, str(user_id))

    last_message = await client.get(key)

    if last_message and last_message == message:
        return True

    await client.set(key, message, ex=DUPLICATE_WINDOW_SECONDS)
    return False


# ======================
# Moderation
# ======================

async def mute_user(room_code: str, user_id: str):
    client = get_redis_client()
    await client.sadd(room_muted_users_key(room_code), str(user_id))


async def unmute_user(room_code: str, user_id: str):
    client = get_redis_client()
    await client.srem(room_muted_users_key(room_code), str(user_id))


async def is_user_muted(room_code: str, user_id: str) -> bool:
    client = get_redis_client()
    return await client.sismember(
        room_muted_users_key(room_code),
        str(user_id),
    )


async def ban_user(room_code: str, user_id: str):
    client = get_redis_client()
    await client.sadd(room_banned_users_key(room_code), str(user_id))


async def is_user_banned(room_code: str, user_id: str) -> bool:
    client = get_redis_client()
    return await client.sismember(
        room_banned_users_key(room_code),
        str(user_id),
    )


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
