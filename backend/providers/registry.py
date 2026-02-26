from dataclasses import dataclass
from typing import Callable

from providers.base import PlaybackSource
from providers.vidking import build_vidking_source, derive_vidking_embed_url


@dataclass(frozen=True)
class ProviderEntry:
    name: str
    build_source: Callable[..., PlaybackSource]
    derive_embed_url: Callable[[PlaybackSource], str]


PROVIDERS = {
    "vidking": ProviderEntry(
        name="vidking",
        build_source=build_vidking_source,
        derive_embed_url=derive_vidking_embed_url,
    ),
}


def get_provider(name: str) -> ProviderEntry:
    provider = PROVIDERS.get(name)
    if not provider:
        raise ValueError(f"Unknown provider: {name}")
    return provider
