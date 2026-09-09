from django.test import TestCase
from providers.resolver import resolve_playback_source, derive_embed_url


class EmbedApiResolverTests(TestCase):
    def test_movie_url(self):
        source = resolve_playback_source(
            provider="embed-api",
            media_type="movie",
            external_id="1078605",
        )
        url = derive_embed_url(source)
        self.assertEqual(
            url,
            "https://watch.embed-api.stream/embed/movie/1078605",
        )

    def test_tv_url(self):
        source = resolve_playback_source(
            provider="embed-api",
            media_type="tv",
            external_id="119051",
            season=1,
            episode=8,
        )
        url = derive_embed_url(source)
        self.assertEqual(
            url,
            "https://watch.embed-api.stream/embed/tv/119051/1/8",
        )
