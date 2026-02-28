from django.test import TestCase
from rest_framework.test import APIClient

from users.models import User


class UsernameFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="test@test.com",
            display_name="Test",
            username=None,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_set_username_success(self):
        res = self.client.post(
            "/api/set-username/",
            {"username": "valid_name"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)

    def test_duplicate_username_rejected(self):
        User.objects.create_user(
            email="x@test.com",
            password="pass",
            username="duplicate",
        )

        res = self.client.post(
            "/api/set-username/",
            {"username": "duplicate"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
