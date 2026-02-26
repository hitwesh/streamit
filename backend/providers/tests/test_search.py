from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync
from django.test import TestCase

from providers.registry import get_provider


class SearchTests(TestCase):
    @patch("providers.vidking.search_tmdb", new_callable=AsyncMock)
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

        provider = get_provider("vidking")
        results = async_to_sync(provider.search)("test")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Test Movie")
        self.assertEqual(results[0].media_type, "movie")
