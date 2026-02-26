# providers/vidking.py

from providers.base import BaseProvider, PlaybackSource
from providers.search_types import ContentSearchResult
from providers.tmdb_client import search_tmdb


VIDKING_BASE_URL = "https://www.vidking.net/embed"


def build_vidking_source(
    *,
    media_type: str,
    external_id: str,
    season: int | None = None,
    episode: int | None = None,
) -> PlaybackSource:
    if media_type not in {"movie", "tv"}:
        raise ValueError("Vidking supports only movie or tv media types")

    if media_type == "tv" and (season is None or episode is None):
        raise ValueError("TV playback requires season and episode")

    return PlaybackSource(
        provider="vidking",
        media_type=media_type,
        external_id=external_id,
        season=season,
        episode=episode,
        supports_events=True,
        supports_progress=True,
        capabilities={
            "seek": True,
            "pause": True,
            "resume": True,
            "autoplay": True,
        },
    )


def derive_vidking_embed_url(source: PlaybackSource) -> str:
    if source.media_type == "movie":
        return f"{VIDKING_BASE_URL}/movie/{source.external_id}"

    return (
        f"{VIDKING_BASE_URL}/tv/"
        f"{source.external_id}/{source.season}/{source.episode}"
    )


class VidkingProvider(BaseProvider):
    name = "vidking"

    async def search(self, query: str, page: int = 1) -> list[ContentSearchResult]:
        data = await search_tmdb(query, page)

        results: list[ContentSearchResult] = []

        for item in data.get("results", []):
            media_type = item.get("media_type")
            if media_type not in ["movie", "tv"]:
                continue

            title = item.get("title") or item.get("name")
            poster_path = item.get("poster_path")
            poster = (
                f"https://image.tmdb.org/t/p/w500{poster_path}"
                if poster_path
                else None
            )

            release_date = item.get("release_date") or item.get("first_air_date")
            release_year = int(release_date[:4]) if release_date else None

            results.append(
                ContentSearchResult(
                    provider="vidking",
                    stream_id=str(item.get("id")),
                    media_type=media_type,
                    title=title or "",
                    poster=poster,
                    release_year=release_year,
                )
            )

        return results
