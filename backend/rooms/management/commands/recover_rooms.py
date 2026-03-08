import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from django.utils import timezone

from common.redis_client import get_redis_client
from common.redis_keys import room_state_key
from rooms.models import Room

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Recover live rooms after server restart"

    def handle(self, *args, **options):
        redis = get_redis_client()
        rooms = Room.objects.filter(state=Room.State.LIVE)

        for room in rooms:
            key = room_state_key(room.code)

            try:
                exists = async_to_sync(redis.exists)(key)
            except Exception as exc:
                logger.error(
                    "Live room recovery skipped due to Redis error.",
                    extra={"room_code": room.code, "error": str(exc)},
                )
                continue

            if exists:
                continue

            now = timezone.now()

            if room.host_disconnected_at:
                grace_deadline = room.host_disconnected_at + timedelta(
                    seconds=Room.GRACE_PERIOD_SECONDS
                )

                room.state = Room.State.GRACE
                room.save(update_fields=["state"])

                if now >= grace_deadline:
                    room.mark_expired()
                    logger.warning(
                        "Live room missing Redis state; grace expired. Marked EXPIRED.",
                        extra={"room_code": room.code},
                    )
                    continue

                logger.warning(
                    "Live room missing Redis state. Moving to GRACE.",
                    extra={"room_code": room.code},
                )
                continue

            room.state = Room.State.GRACE
            room.host_disconnected_at = now
            room.save(update_fields=["state", "host_disconnected_at"])

            logger.warning(
                "Live room missing Redis state. Moving to GRACE.",
                extra={"room_code": room.code},
            )

        self.stdout.write(self.style.SUCCESS("Room recovery completed"))
