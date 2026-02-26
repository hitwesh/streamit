from dataclasses import dataclass
from typing import Optional


@dataclass
class ContentSearchResult:
    provider: str
    stream_id: str
    media_type: str  # "movie" or "tv"
    title: str
    poster: Optional[str]
    release_year: Optional[int]
