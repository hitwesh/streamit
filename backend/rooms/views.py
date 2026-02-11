from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from asgiref.sync import async_to_sync

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

import json

from .models import Room, RoomParticipant, WatchProgress
from common.redis_client import get_redis_client
from common.redis_keys import (
    room_host_status_key,
    room_viewers_key,
)
from .serializers import WatchProgressSerializer
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_room_view(request):
    room_id = request.data.get("room_id")

    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)

    if room.host != request.user:
        return Response({"error": "Only host can delete room"}, status=403)

    room.is_active = False
    room.save(update_fields=["is_active"])

    return Response({"status": "room_deleted"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_progress_view(request):
    data = request.data

    room_id = data.get("room_id")
    if not room_id:
        return Response({"error": "room_id required"}, status=400)

    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)

    progress, _ = WatchProgress.objects.update_or_create(
        user=request.user,
        room=room,
        media_id=data.get("media_id"),
        media_type=data.get("media_type"),
        season=data.get("season"),
        episode=data.get("episode"),
        defaults={
            "timestamp": data.get("timestamp", 0),
            "duration": data.get("duration", 0),
            "progress_percent": data.get("progress_percent", 0),
        },
    )

    serializer = WatchProgressSerializer(progress)
    return Response(serializer.data, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_progress_view(request):
    room_id = request.query_params.get("room_id")
    media_id = request.query_params.get("media_id")
    media_type = request.query_params.get("media_type")

    if not room_id or not media_id or not media_type:
        return Response(
            {"error": "room_id, media_id and media_type required"},
            status=400,
        )

    try:
        progress = WatchProgress.objects.get(
            user=request.user,
            room_id=room_id,
            media_id=media_id,
            media_type=media_type,
        )
    except WatchProgress.DoesNotExist:
        return Response({"progress": None}, status=200)

    serializer = WatchProgressSerializer(progress)
    return Response(serializer.data, status=200)


@api_view(["GET"])
def public_rooms_view(request):
    rooms = list(
        Room.objects.filter(
            is_private=False,
            is_active=True,
            state=Room.State.LIVE,
        )
        .only("code", "host", "created_at")
        .select_related("host")
        .order_by("-created_at")
    )

    async def build_response(rooms_list):
        client = get_redis_client()
        response = []

        for room in rooms_list:
            host_status = await client.get(room_host_status_key(room.code))
            if not host_status:
                continue

            host_payload = json.loads(host_status)
            if host_payload.get("status") != "connected":
                continue

            viewers = await client.get(room_viewers_key(room.code))

            response.append({
                "code": room.code,
                "host": room.host.display_name,
                "viewers": int(viewers or 0),
                "created_at": room.created_at.isoformat(),
            })

        return response

    data = async_to_sync(build_response)(rooms)
    return Response(data)
