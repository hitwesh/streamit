from django.test import TestCase
from rest_framework.test import APIClient

from rooms.models import Room, WatchProgress
from users.models import User


class WatchProgressTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass",
            display_name="User",
        )

        self.room = Room.objects.create(
            code="PROG01",
            host=self.user,
            video_provider="x",
            video_id="y",
        )

        self.client.force_authenticate(user=self.user)

    def test_save_progress(self):
        res = self.client.post(
            "/api/rooms/progress/save/",
            {
                "room_id": str(self.room.id),
                "media_id": "299534",
                "media_type": "movie",
                "timestamp": 120,
                "duration": 7200,
                "progress_percent": 1.6,
            },
            format="json",
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(WatchProgress.objects.count(), 1)

    def test_get_progress(self):
        WatchProgress.objects.create(
            user=self.user,
            room=self.room,
            media_id="299534",
            media_type="movie",
            timestamp=200,
            duration=7200,
            progress_percent=2.7,
        )

        res = self.client.get(
            f"/api/rooms/progress/get/?room_id={self.room.id}&media_id=299534&media_type=movie"
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["timestamp"], 200)
