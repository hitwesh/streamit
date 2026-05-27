import json
import os

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
