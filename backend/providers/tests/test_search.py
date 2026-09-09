from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync
from django.test import TestCase

from providers.registry import get_provider
from providers import tmdb_client


class SearchTests(TestCase):
    @patch("providers.embed_api.search_tmdb", new_callable=AsyncMock)
    def test_search_returns_normalized_results(self, mock_search):
        mock_search.return_value = {
            "results": [
                {
                    "id": 123,
                    "media_type": "movie",
                    "title": "Test Movie",
                    "poster_path": "/poster.jpg",
                    "release_date": "2020-01-01",
                }
            ]
        }

        provider = get_provider("embed-api")
        results = async_to_sync(provider.search)("test")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Test Movie")
        self.assertEqual(results[0].media_type, "movie")

    @patch.object(tmdb_client, "TMDB_API_KEY", "eyJread-access-token")
    def test_read_access_token_uses_bearer_authentication(self):
        headers, params = tmdb_client._authentication_options()

        self.assertEqual(headers, {"Authorization": "Bearer eyJread-access-token"})
        self.assertEqual(params, {})

    @patch.object(tmdb_client, "TMDB_API_KEY", "legacy-api-key")
    def test_legacy_api_key_uses_query_authentication(self):
        headers, params = tmdb_client._authentication_options()

        self.assertEqual(headers, {})
        self.assertEqual(params, {"api_key": "legacy-api-key"})
