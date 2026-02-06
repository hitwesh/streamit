import json
import os

from django.test import Client, TestCase

from users.models import User


TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "test-password")


class RoomAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="user@test.com",
            password=TEST_PASSWORD,
            display_name="User",
        )
        self.client.login(email="user@test.com", password=TEST_PASSWORD)

    def test_create_room(self):
        response = self.client.post(
            "/api/rooms/create/",
            data=json.dumps({"is_private": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("code", response.json())

    def test_join_room(self):
        create = self.client.post(
            "/api/rooms/create/",
            data=json.dumps({"is_private": False}),
            content_type="application/json",
        )
        code = create.json()["code"]

        join = self.client.post(
            "/api/rooms/join/",
            data=json.dumps({"code": code}),
            content_type="application/json",
        )

        self.assertEqual(join.status_code, 200)
        self.assertTrue(join.json()["is_host"])
