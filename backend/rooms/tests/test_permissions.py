from django.test import TestCase

from rooms.models import Room
from rooms.permissions import PermissionService
from users.models import User


class PermissionTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email="host@test.com",
            password="pass",
            username="host",
            display_name="Host",
        )

        self.guest = User.objects.create(
            email="guest@test.com",
            username="guest",
            is_guest=True,
            display_name="Guest",
        )

        self.room = Room.objects.create(
            code="PERM01",
            host=self.host,
            video_provider="movie",
            video_id="x",
        )

    def test_host_can_control(self):
        self.assertTrue(
            PermissionService.can_control_playback(self.host, self.room)
        )

    def test_guest_cannot_host(self):
        self.assertFalse(
            PermissionService.can_host(self.guest)
        )
