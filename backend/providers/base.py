# providers/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

from providers.search_types import ContentSearchResult


@dataclass(frozen=True)
class PlaybackSource:
    provider: str
    media_type: str  # "movie" | "tv"
    external_id: str
    season: Optional[int] = None
    episode: Optional[int] = None

    supports_events: bool = False
    supports_progress: bool = False

    capabilities: Dict[str, bool] = None


class BaseProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, page: int = 1) -> List[ContentSearchResult]:
        """
        Search provider content and return normalized results.
        """
        raise NotImplementedError
