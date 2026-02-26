from providers.base import BaseProvider
from providers.vidking import VidkingProvider


PROVIDERS: dict[str, BaseProvider] = {
    "vidking": VidkingProvider(),
}


def get_provider(name: str) -> BaseProvider:
    provider = PROVIDERS.get(name)
    if not provider:
        raise ValueError(f"Unknown provider: {name}")
    return provider
