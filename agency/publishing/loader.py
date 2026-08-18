"""Liest ein erzeugtes Review-Paket (/output/{datum}/{plattform}/) in Post-Objekte."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .base import Post

_HEADING = re.compile(r"^\s*#{1,6}\s")
_POST_SPLIT = re.compile(r"^###\s+Post\s+\d+", re.IGNORECASE | re.MULTILINE)


def extract_variant(post_md: str, variant: int = 1) -> str:
    """Zieht den reinen Text einer Post-Variante aus post.md (ohne Überschriften)."""
    parts = _POST_SPLIT.split(post_md or "")
    # parts[0] ist alles vor dem ersten "### Post" (meist die "## Plattform"-Zeile).
    bodies = [p for p in parts[1:]] if len(parts) > 1 else [post_md or ""]
    idx = min(max(variant - 1, 0), len(bodies) - 1)
    body = bodies[idx]
    lines = [ln for ln in body.splitlines() if not _HEADING.match(ln)]
    return "\n".join(lines).strip()


def load_post(day_dir: Path, platform_key: str, variant: int = 1) -> Post:
    """Baut aus post.md + meta.json + broll/ ein Post-Objekt für eine Plattform."""
    pdir = day_dir / platform_key
    post_md = (pdir / "post.md").read_text(encoding="utf-8") if (pdir / "post.md").exists() else ""
    text = extract_variant(post_md, variant)

    meta = {}
    if (pdir / "meta.json").exists():
        meta = json.loads((pdir / "meta.json").read_text(encoding="utf-8"))

    media: list[Path] = []
    broll = pdir / "broll"
    if broll.exists():
        media = sorted(broll.glob("*.mp4"))

    return Post(
        platform=platform_key,
        text=text,
        title=meta.get("titel"),
        description=meta.get("description"),
        media=media,
    )
