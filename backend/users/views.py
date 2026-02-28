import json
import re
import uuid

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .models import User


@csrf_exempt
@require_POST
def login_view(request):
    data = json.loads(request.body)
    email = data.get("email")
    password = data.get("password")

    user = authenticate(request, email=email, password=password)
    if user is None:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend"
    )

    # 🔐 JWT for WebSocket & API auth
    token = AccessToken.for_user(user)

    return JsonResponse({
        "id": str(user.id),
        "display_name": user.display_name,
        "is_guest": user.is_guest,
        "access_token": str(token),
    })


@csrf_exempt
@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"success": True})


@csrf_exempt
@require_POST
def guest_login_view(request):
    data = json.loads(request.body)
    display_name = data.get("display_name")

    if not display_name:
        return JsonResponse({"error": "Display name required"}, status=400)

    user = User.objects.create_user(
        email=None,
        password=None,
        display_name=display_name,
        is_guest=True,
    )

    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend"
    )

    token = AccessToken.for_user(user)

    return JsonResponse({
        "id": str(user.id),
        "display_name": user.display_name,
        "is_guest": True,
        "access_token": str(token),
    })


@api_view(["POST"])
def guest_login(request):
    guest_username = f"Guest-{uuid.uuid4().hex[:6]}"
    guest_user = User.objects.create_user(
        email=f"{uuid.uuid4()}@guest.local",
        username=guest_username,
        display_name=guest_username,
        is_guest=True,
    )

    refresh = RefreshToken.for_user(guest_user)

    return Response({
        "access": str(refresh.access_token),
        "username": guest_user.username,
        "role": "guest",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_username(request):
    username = (request.data.get("username") or "").strip()

    if not username:
        return Response({"error": "Username required"}, status=400)

    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        return Response(
            {"error": "Username must be 3-20 chars, alphanumeric or underscore"},
            status=400,
        )

    if (
        User.objects
        .filter(username__iexact=username)
        .exclude(pk=request.user.pk)
        .exists()
    ):
        return Response({"error": "Username already taken"}, status=400)

    user = request.user
    user.username = username
    user.display_name = username
    user.save()

    return Response({"status": "ok"})
