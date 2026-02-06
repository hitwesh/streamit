import redis.asyncio as redis
from django.conf import settings


def get_redis_url():
    return getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")


def get_redis_client():
    """
    Async Redis clients are event-loop bound and must not be cached.
    """
    return redis.from_url(
        get_redis_url(),
        decode_responses=True,
    )
