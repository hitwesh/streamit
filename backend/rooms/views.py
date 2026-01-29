from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Room
from .services import create_room


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
