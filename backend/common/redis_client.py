from functools import lru_cache

import redis.asyncio as redis
from django.conf import settings


def get_redis_url():
    return getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")


@lru_cache(maxsize=1)
def get_redis_client():
    return redis.from_url(get_redis_url(), decode_responses=True)
