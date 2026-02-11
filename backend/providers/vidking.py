# providers/vidking.py

from providers.base import PlaybackSource


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
