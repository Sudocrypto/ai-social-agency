"""Plattform-Specs für X, Instagram, Facebook, YouTube.

Zentral, damit Copywriter, SEO und Publisher dieselben Regeln benutzen.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformSpec:
    key: str
    name: str
    max_chars: int          # weicher Richtwert für den Haupttext
    hashtag_count: str      # empfohlene Hashtag-Menge
    format_hint: str        # Kurzbeschreibung des idealen Formats
    supports_video: bool


PLATFORMS: dict[str, PlatformSpec] = {
    "x": PlatformSpec(
        key="x",
        name="X (Twitter)",
        max_chars=280,
        hashtag_count="1–2",
        format_hint="Knackiger Hook, ggf. Thread (nummerierte Posts), pointiert.",
        supports_video=True,
    ),
    "instagram": PlatformSpec(
        key="instagram",
        name="Instagram",
        max_chars=2200,
        hashtag_count="8–15",
        format_hint="Starker erster Satz (vor 'mehr'), Story-Caption, klarer CTA. Reels für Video.",
        supports_video=True,
    ),
    "facebook": PlatformSpec(
        key="facebook",
        name="Facebook",
        max_chars=2000,
        hashtag_count="2–5",
        format_hint="Etwas ausführlicher, community-orientiert, Frage am Ende für Engagement.",
        supports_video=True,
    ),
    "youtube": PlatformSpec(
        key="youtube",
        name="YouTube",
        max_chars=5000,
        hashtag_count="3–5",
        format_hint="Titel + SEO-Description mit Timestamps/Keywords. Langform-Video + Shorts.",
        supports_video=True,
    ),
}

# Reihenfolge bei --platform all.
ALL_PLATFORMS = ["x", "instagram", "facebook", "youtube"]


def resolve_platforms(platform: str) -> list[str]:
    """'all' -> alle; sonst die eine Plattform (validiert)."""
    if platform == "all":
        return list(ALL_PLATFORMS)
    if platform not in PLATFORMS:
        raise ValueError(
            f"Unbekannte Plattform '{platform}'. "
            f"Erlaubt: {', '.join([*ALL_PLATFORMS, 'all'])}"
        )
    return [platform]


def spec(platform_key: str) -> PlatformSpec:
    return PLATFORMS[platform_key]
