import os

import httpx

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"


async def search_tmdb(query: str, page: int = 1) -> dict:
    if not TMDB_API_KEY:
        raise ValueError("TMDB_API_KEY is not configured")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/search/multi",
            params={
                "api_key": TMDB_API_KEY,
                "query": query,
                "page": page,
            },
        )
        response.raise_for_status()
        return response.json()
