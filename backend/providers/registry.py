from providers.base import BaseProvider
from providers.embed_api import EmbedApiProvider


PROVIDERS: dict[str, BaseProvider] = {
    "embed-api": EmbedApiProvider(),
}


def get_provider(name: str) -> BaseProvider:
    provider = PROVIDERS.get(name)
    if not provider:
        raise ValueError(f"Unknown provider: {name}")
    return provider
