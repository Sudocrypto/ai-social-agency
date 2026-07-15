"""Ruft öffentliche YouTube-Statistiken über die YouTube Data API v3 ab.

Nutzt nur einen API-Key (kein OAuth) – für öffentliche Videos genügt das für
Views/Likes/Kommentare. Ohne Key/Netz läuft der Rest des Monitorings (Report aus
vorhandenen Daten) trotzdem.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

API_URL = "https://www.googleapis.com/youtube/v3/videos"


def _to_int(val) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def fetch_stats(video_ids: list[str], api_key: str) -> list[dict]:
    """Holt Statistiken für bis zu vielen Video-IDs (in 50er-Batches).

    Rückgabe je Video: {video_id, titel, views, likes, comments}.
    """
    if not api_key:
        raise RuntimeError(
            "YOUTUBE_API_KEY fehlt. In .env eintragen (YouTube Data API v3, nur API-Key)."
        )
    results: list[dict] = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        params = urllib.parse.urlencode(
            {"part": "statistics,snippet", "id": ",".join(batch), "key": api_key}
        )
        with urllib.request.urlopen(f"{API_URL}?{params}", timeout=30) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
        for item in data.get("items", []):
            stats = item.get("statistics", {})
            results.append(
                {
                    "video_id": item.get("id", ""),
                    "titel": item.get("snippet", {}).get("title", ""),
                    "views": _to_int(stats.get("viewCount")),
                    "likes": _to_int(stats.get("likeCount")),
                    "comments": _to_int(stats.get("commentCount")),
                }
            )
    return results
