from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

import json

from .models import Room
from .services import create_room
from .services import create_room, join_room

@csrf_exempt
@require_POST
@login_required
def create_room_view(request):
    data = json.loads(request.body)

    is_private = data.get("is_private", False)
    entry_mode = data.get("entry_mode")

    if is_private:
        if entry_mode not in [Room.ENTRY_APPROVAL, Room.ENTRY_PASSWORD]:
            return JsonResponse(
                {"error": "Invalid entry_mode for private room"},
                status=400
            )

    room, raw_password = create_room(
        host=request.user,
        is_private=is_private,
        entry_mode=entry_mode,
    )

    response = {
        "room_id": str(room.id),
        "code": room.code,
        "is_private": room.is_private,
        "entry_mode": room.entry_mode,
    }

    if raw_password:
        response["room_password"] = raw_password  # shown ONCE

    return JsonResponse(response, status=201)

@csrf_exempt
@require_POST
@login_required
def join_room_view(request):
    data = json.loads(request.body)
    room_code = data.get("code")
    password = data.get("password")

    if not room_code:
        return JsonResponse({"error": "Room code required"}, status=400)

    try:
        participant, room = join_room(
            room_code=room_code,
            user=request.user,
            password=password,
        )
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=403)

    return JsonResponse({
        "room_id": str(room.id),
        "code": room.code,
        "status": participant.status,
        "is_host": room.host_id == request.user.id,
    })

@csrf_exempt
@require_POST
@login_required
def approve_participant_view(request):
    data = json.loads(request.body)
    room_id = data.get("room_id")
    user_id = data.get("user_id")

    room = get_object_or_404(Room, id=room_id)

    if room.host_id != request.user.id:
        return JsonResponse({"error": "Only host can approve"}, status=403)

    participant = get_object_or_404(
        RoomParticipant,
        room=room,
        user_id=user_id,
        status=RoomParticipant.STATUS_PENDING,
    )

    participant.status = RoomParticipant.STATUS_APPROVED
    participant.save()

    return JsonResponse({"approved": True})
