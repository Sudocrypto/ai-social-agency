"""Zuordnung Plattform-Key -> Publisher-Instanz."""

from __future__ import annotations

from .base import PlatformPublisher
from .meta_publisher import FacebookPublisher, InstagramPublisher
from .x_publisher import XPublisher
from .youtube_publisher import YouTubePublisher

PUBLISHERS: dict[str, PlatformPublisher] = {
    "x": XPublisher(),
    "instagram": InstagramPublisher(),
    "facebook": FacebookPublisher(),
    "youtube": YouTubePublisher(),
}


def get_publisher(platform_key: str) -> PlatformPublisher:
    if platform_key not in PUBLISHERS:
        raise ValueError(
            f"Kein Publisher für '{platform_key}'. "
            f"Verfügbar: {', '.join(PUBLISHERS)}"
        )
    return PUBLISHERS[platform_key]
