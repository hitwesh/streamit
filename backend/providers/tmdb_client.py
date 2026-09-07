import os

import httpx

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"


def _authentication_options() -> tuple[dict[str, str], dict[str, str]]:
    if not TMDB_API_KEY:
        raise ValueError("TMDB_API_KEY is not configured")

    # TMDB Read Access Tokens are JWTs and must be sent as Bearer tokens.
    if TMDB_API_KEY.startswith("eyJ"):
        return {"Authorization": f"Bearer {TMDB_API_KEY}"}, {}

    return {}, {"api_key": TMDB_API_KEY}


async def search_tmdb(query: str, page: int = 1) -> dict:
    headers, params = _authentication_options()
    params.update({"query": query, "page": str(page)})

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/search/multi",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
