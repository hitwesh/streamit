from django.test import TestCase
from providers.resolver import resolve_playback_source, derive_embed_url


class VidkingResolverTests(TestCase):
    def test_movie_url(self):
        source = resolve_playback_source(
            provider="vidking",
            media_type="movie",
            external_id="1078605",
        )
        url = derive_embed_url(source)
        self.assertEqual(
            url,
            "https://www.vidking.net/embed/movie/1078605",
        )

    def test_tv_url(self):
        source = resolve_playback_source(
            provider="vidking",
            media_type="tv",
            external_id="119051",
            season=1,
            episode=8,
        )
        url = derive_embed_url(source)
        self.assertEqual(
            url,
            "https://www.vidking.net/embed/tv/119051/1/8",
        )
