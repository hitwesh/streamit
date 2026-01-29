from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import User
import json
import uuid

@csrf_exempt
@require_POST
def login_view(request):
    data = json.loads(request.body)
    email = data.get("email")
    password = data.get("password")

    user = authenticate(request, username=email, password=password)
    if user is None:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    login(request, user)
    return JsonResponse({
        "id": str(user.id),
        "display_name": user.display_name,
        "is_guest": user.is_guest,
    })

@csrf_exempt
@require_POST
def login_view(request):
    data = json.loads(request.body)
    email = data.get("email")
    password = data.get("password")

    user = authenticate(request, email=email, password=password)
    if user is None:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    login(request, user)
    return JsonResponse({
        "id": str(user.id),
        "display_name": user.display_name,
        "is_guest": user.is_guest,
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

    login(request, user)

    return JsonResponse({
        "id": str(user.id),
        "display_name": user.display_name,
        "is_guest": True,
    })
