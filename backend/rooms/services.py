import random
import string
from .models import Room, RoomParticipant


def generate_room_code(length=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def create_room(*, host, is_private, entry_mode):
    # Generate unique room code
    while True:
        code = generate_room_code()
        if not Room.objects.filter(code=code).exists():
            break

    room = Room.objects.create(
        code=code,
        host=host,
        is_private=is_private,
        entry_mode=entry_mode if is_private else None,
        video_provider="",
        video_id="",
    )

    raw_password = None
    if is_private and entry_mode == Room.ENTRY_PASSWORD:
        raw_password = room.set_entry_password()
        room.save()

    # Host is always an approved participant
    RoomParticipant.objects.create(
        room=room,
        user=host,
        status=RoomParticipant.STATUS_APPROVED,
    )

    return room, raw_password
