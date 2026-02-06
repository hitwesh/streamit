from django.test import TestCase

from rooms.models import RoomParticipant
from rooms.services import create_room, join_room
from users.models import User


class RoomJoinTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            email="hiteshroy0001@gmail.com",
            password="Notimetodie007",
            display_name="Host",
        )
        self.user = User.objects.create_user(
            email="user@test.com",
            password="password",
            display_name="UserB",
        )

        self.room, _ = create_room(
            host=self.host,
            is_private=False,
            entry_mode=None,
        )

    def test_host_is_auto_approved(self):
        self.assertTrue(
            RoomParticipant.objects.filter(
                room=self.room,
                user=self.host,
                status=RoomParticipant.STATUS_APPROVED,
            ).exists()
        )

    def test_join_public_room(self):
        participant, room = join_room(
            room_code=self.room.code,
            user=self.user,
        )

        self.assertEqual(participant.status, RoomParticipant.STATUS_APPROVED)

    def test_join_idempotent(self):
        join_room(room_code=self.room.code, user=self.user)
        participant2, _ = join_room(room_code=self.room.code, user=self.user)

        self.assertEqual(
            RoomParticipant.objects.filter(room=self.room, user=self.user).count(),
            1,
        )
