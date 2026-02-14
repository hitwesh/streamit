from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from rooms.models import Room, WatchProgress
from users.models import User


class ResumeAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass",
            display_name="User",
        )

        self.room = Room.objects.create(
            code="RES123",
            host=self.user,
            video_provider="movie",
            video_id="x",
        )

        self.client = APIClient()
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_no_progress_returns_zero(self):
        res = self.client.get(f"/api/rooms/{self.room.code}/resume/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["progress_percent"], 0)
        self.assertEqual(res.json()["last_position_seconds"], 0)
        self.assertFalse(res.json()["completed"])

    def test_returns_existing_progress(self):
        WatchProgress.objects.create(
            user=self.user,
            room=self.room,
            media_id="299534",
            media_type="movie",
            timestamp=300,
            progress_percent=55.0,
            completed=False,
        )

        res = self.client.get(f"/api/rooms/{self.room.code}/resume/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["progress_percent"], 55.0)
        self.assertEqual(res.json()["last_position_seconds"], 300)
