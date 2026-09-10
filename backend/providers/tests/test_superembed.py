from django.test import TestCase
from providers.resolver import resolve_playback_source, derive_embed_url


class SuperEmbedResolverTests(TestCase):
    def test_movie_url(self):
        source = resolve_playback_source(
            provider="superembed",
            media_type="movie",
            external_id="447365",
        )
        url = derive_embed_url(source)
        self.assertEqual(
            url,
            "https://multiembed.mov/?video_id=447365&tmdb=1",
        )

    def test_tv_url(self):
        source = resolve_playback_source(
            provider="superembed",
            media_type="tv",
            external_id="114472",
            season=1,
            episode=2,
        )
        url = derive_embed_url(source)
        self.assertEqual(
            url,
            "https://multiembed.mov/?video_id=114472&tmdb=1&s=1&e=2",
        )

    def test_tv_requires_season_and_episode(self):
        with self.assertRaises(ValueError):
            resolve_playback_source(
                provider="superembed",
                media_type="tv",
                external_id="114472",
            )
