from django.test import TestCase

from rooms.models import RoomPlaybackState
from rooms.services import create_room
from users.models import User


class PlaybackAuthorityTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password="pass",
            display_name="Host",
        )
        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass",
            display_name="User",
        )

        self.room, _ = create_room(
            host=self.host,
            is_private=False,
            entry_mode=None,
        )

    def test_playback_state_created(self):
        state, _ = RoomPlaybackState.objects.get_or_create(room=self.room)
        self.assertFalse(state.is_playing)
        self.assertEqual(state.current_time, 0.0)
