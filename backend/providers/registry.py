from providers.base import BaseProvider
from providers.embed_api import EmbedApiProvider
from providers.superembed import SuperEmbedProvider


PROVIDERS: dict[str, BaseProvider] = {
    "embed-api": EmbedApiProvider(),
    "superembed": SuperEmbedProvider(),
}


def get_provider(name: str) -> BaseProvider:
    provider = PROVIDERS.get(name)
    if not provider:
        raise ValueError(f"Unknown provider: {name}")
    return provider
