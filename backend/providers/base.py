# providers/base.py

from dataclasses import dataclass
from typing import Optional, Dict


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
