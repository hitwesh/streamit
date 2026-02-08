from datetime import timedelta

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from django.utils import timezone

from common.redis_client import get_redis_client
from common.redis_keys import (
    room_host_status_key,
    room_participants_key,
    room_state_key,
)
from common.redis_room_state import clear_grace
from rooms.models import Room


class Command(BaseCommand):
    help = "Expire rooms whose host grace period has elapsed"

    def handle(self, *args, **options):
        now = timezone.now()

        grace_rooms = Room.objects.filter(
            state=Room.State.GRACE,
            is_active=True,
        )

        expired_count = 0

        for room in grace_rooms:
            if not room.host_disconnected_at:
                continue

            grace_deadline = room.host_disconnected_at + timedelta(
                seconds=Room.GRACE_PERIOD_SECONDS
            )

            if now >= grace_deadline:
                self.expire_room(room)
                expired_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Expired {expired_count} room(s)")
        )

    def expire_room(self, room: Room):
        if room.state == Room.State.DELETED:
            return
        # 1) Update DB (authoritative)
        room.mark_expired()

        # 2) Cleanup Redis (best-effort)
        async_to_sync(self._cleanup_redis)(room)

    async def _cleanup_redis(self, room: Room):
        client = get_redis_client()

        await client.delete(room_state_key(room.code))
        await client.delete(room_participants_key(room.code))
        await client.delete(room_host_status_key(room.code))

        # Grace key may already be gone -- safe to call
        await clear_grace(room.code)
