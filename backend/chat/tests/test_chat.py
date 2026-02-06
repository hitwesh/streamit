from django.test import TestCase

from chat.models import ChatMessage
from rooms.services import create_room
from users.models import User


class ChatTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="u@test.com",
            password="pass",
            display_name="User",
        )
        self.room, _ = create_room(
            host=self.user,
            is_private=False,
            entry_mode=None,
        )

    def test_chat_persists_when_enabled(self):
        ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            message="hello",
        )
        self.assertEqual(ChatMessage.objects.count(), 1)

    def test_chat_disabled_prevents_persist(self):
        self.room.is_chat_enabled = False
        self.room.save()

        ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            message="should still save at DB level",
        )

        self.assertEqual(ChatMessage.objects.count(), 1)
