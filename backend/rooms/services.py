import random
import string
from .models import Room, RoomParticipant
from django.shortcuts import get_object_or_404


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

def join_room(*, room_code, user, password=None):
    room = get_object_or_404(Room, code=room_code)

    # Already joined → return success
    participant = RoomParticipant.objects.filter(room=room, user=user).first()
    if participant:
        return participant, room

    # PUBLIC ROOM
    if not room.is_private:
        participant = RoomParticipant.objects.create(
            room=room,
            user=user,
            status=RoomParticipant.STATUS_APPROVED,
        )
        return participant, room

    # PRIVATE ROOM
    if room.entry_mode == Room.ENTRY_PASSWORD:
        if not password or not room.check_entry_password(password):
            raise ValueError("Invalid room password")

        participant = RoomParticipant.objects.create(
            room=room,
            user=user,
            status=RoomParticipant.STATUS_APPROVED,
        )
        return participant, room

    # APPROVAL ROOM
    participant = RoomParticipant.objects.create(
        room=room,
        user=user,
        status=RoomParticipant.STATUS_PENDING,
    )
    return participant, room


def get_public_rooms():
    return (
        Room.objects
        .filter(
            is_private=False,
            is_active=True,
            state__in=[Room.State.LIVE, Room.State.GRACE],
        )
        .only("code", "host", "created_at")
        .select_related("host")
        .order_by("-created_at")
    )