# providers/resolver.py

from providers.vidking import (
    build_vidking_source,
    derive_vidking_embed_url,
)
from providers.base import PlaybackSource


def resolve_playback_source(
    *,
    provider: str,
    media_type: str,
    external_id: str,
    season: int | None = None,
    episode: int | None = None,
) -> PlaybackSource:
    if provider == "vidking":
        return build_vidking_source(
            media_type=media_type,
            external_id=external_id,
            season=season,
            episode=episode,
        )

    raise ValueError(f"Unsupported playback provider: {provider}")


def derive_embed_url(source: PlaybackSource) -> str:
    if source.provider == "vidking":
        return derive_vidking_embed_url(source)

    raise ValueError(f"No embed URL resolver for provider: {source.provider}")
