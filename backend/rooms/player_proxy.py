"""
player_proxy.py

Django view that replicates se_player.php behaviour:
  1. Accept video_id, tmdb, s/season, e/episode query params
  2. Make a server-side HTTP GET to getsuperembed.link with those params
  3. Redirect the browser to the returned direct-stream URL

This allows the iframe src to point at our own origin
  /api/player/?video_id=...&tmdb=1
instead of multiembed.mov directly, bypassing their X-Frame-Options header.
"""

import httpx

from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_GET

SUPEREMBED_API = "https://getsuperembed.link/"

# Player appearance — kept in sync with se_player.php defaults
_PLAYER_PARAMS = {
    "player_font": "Poppins",
    "player_bg_color": "000000",
    "player_font_color": "ffffff",
    "player_primary_color": "34cfeb",
    "player_secondary_color": "6900e0",
    "player_loader": "1",
    "preferred_server": "0",
    "player_sources_toggle_type": "2",
}


@require_GET
def player_proxy_view(request):
    video_id = request.GET.get("video_id", "").strip()
    if not video_id:
        return HttpResponseBadRequest("Missing video_id")

    tmdb = request.GET.get("tmdb", "0")
    season = request.GET.get("s") or request.GET.get("season") or "0"
    episode = request.GET.get("e") or request.GET.get("episode") or "0"

    params = {
        "video_id": video_id,
        "tmdb": tmdb,
        "season": season,
        "episode": episode,
        **_PLAYER_PARAMS,
    }

    try:
        with httpx.Client(timeout=8, follow_redirects=True) as client:
            resp = client.get(SUPEREMBED_API, params=params)
            player_url = resp.text.strip()
    except httpx.RequestError as exc:
        return HttpResponse(f"Upstream error: {exc}", status=502)

    if not player_url.startswith("https://"):
        # getsuperembed.link returned an error message instead of a URL
        return HttpResponse(f"Player error: {player_url}", status=502)

    return HttpResponseRedirect(player_url)
