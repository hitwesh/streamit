from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from users.models import User


class TokenRefreshTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="refresh@test.com",
            password="test-password",
            display_name="Refresh User",
        )

    def test_login_returns_refresh_token_that_can_refresh_access(self):
        login = self.client.post(
            "/api/auth/login/",
            {"email": "refresh@test.com", "password": "test-password"},
            format="json",
        )

        self.assertEqual(login.status_code, 200)
        login_data = login.json()
        self.assertIn("refresh_token", login_data)

        refreshed = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": login_data["refresh_token"]},
            format="json",
        )

        self.assertEqual(refreshed.status_code, 200)
        self.assertIn("access", refreshed.data)
        self.assertTrue(AccessToken(refreshed.data["access"]))

    def test_refresh_endpoint_rejects_invalid_token(self):
        response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": str(RefreshToken.for_user(self.user))[:-1] + "x"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
