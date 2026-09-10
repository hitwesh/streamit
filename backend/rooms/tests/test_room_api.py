import json
import os
import httpx
from unittest.mock import AsyncMock, patch

from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from users.models import User


TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "test-password")


class RoomAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com",
            password=TEST_PASSWORD,
            display_name="User",
        )

        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_room(self):
        response = self.client.post(
            "/api/rooms/create/",
            {"is_private": False, "genre": "Movies"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("code", response.data)

    def test_join_room(self):
        create = self.client.post(
            "/api/rooms/create/",
            {"is_private": False, "genre": "Movies"},
            format="json",
        )
        code = create.data["code"]

        join = self.client.post(
            "/api/rooms/join/",
            {"code": code},
            format="json",
        )

        self.assertEqual(join.status_code, 200)
        self.assertTrue(join.data["is_host"])

    def test_host_can_update_room_settings(self):
        create = self.client.post(
            "/api/rooms/create/",
            {"is_private": False, "genre": "Movies"},
            format="json",
        )

        response = self.client.post(
            "/api/rooms/settings/",
            {
                "room_id": create.data["room_id"],
                "is_private": True,
                "entry_mode": "APPROVAL",
                "is_chat_enabled": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_private"])
        self.assertEqual(response.data["entry_mode"], "APPROVAL")
        self.assertFalse(response.data["is_chat_enabled"])

    @patch("rooms.views.get_provider")
    def test_search_reports_provider_authentication_failure(self, mock_get_provider):
        request = httpx.Request("GET", "https://api.themoviedb.org/3/search/multi")
        response = httpx.Response(401, request=request)
        provider = mock_get_provider.return_value
        provider.name = "embed-api"
        provider.search = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "invalid credentials",
                request=request,
                response=response,
            )
        )

        result = self.client.get("/api/rooms/search/?q=blue+velvet")

        self.assertEqual(result.status_code, 502)
        self.assertIn("TMDB_API_KEY", result.json()["error"])
