import os

from django.test import TestCase

from rooms.models import Room, RoomPlaybackState
from users.models import User


TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "test-password")


class PlaybackLogicTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password=TEST_PASSWORD,
            display_name="Host",
        )
        self.user = User.objects.create_user(
            email="user@test.com",
            password=TEST_PASSWORD,
            display_name="User",
        )
        self.room = Room.objects.create(
            code="ROOM1",
            host=self.host,
            video_provider="",
            video_id="",
        )

    def test_playback_state_updates(self):
        state = RoomPlaybackState.objects.create(room=self.room)
        state.is_playing = True
        state.current_time = 10
        state.version = 1
        state.save()

        state.refresh_from_db()
        self.assertTrue(state.is_playing)
        self.assertEqual(state.current_time, 10)
        self.assertEqual(state.version, 1)
