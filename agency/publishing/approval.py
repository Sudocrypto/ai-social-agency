"""Liest die Freigabe des Creative Directors pro Plattform aus director_review.md.

Der Director ist die finale Freigabe-Instanz. Diese Freigabe wird beim Posten
durchgesetzt: Plattformen mit "⚠️ NACHBESSERN" werden ohne --force nicht gepostet.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..platforms import ALL_PLATFORMS, spec

_HEADING = re.compile(r"^#{1,6}\s+(.*)$")


def parse_approvals(director_md: str) -> dict[str, dict]:
    """Ordnet jeder Plattform ihren Freigabe-Status zu.

    Rückgabe: {platform_key: {"approved": bool | None, "status": str}}
    approved=True bei FREIGABE, False bei NACHBESSERN, None wenn kein Urteil.
    """
    result: dict[str, dict] = {}
    current: str | None = None

    for line in (director_md or "").splitlines():
        m = _HEADING.match(line)
        if m:
            heading = m.group(1).strip().lower()
            current = _match_platform(heading)
            continue
        if current and current not in result:
            up = line.upper()
            if "NACHBESSERN" in up:
                result[current] = {"approved": False, "status": line.strip()}
            elif "FREIGABE" in up or "✅" in line:
                result[current] = {"approved": True, "status": line.strip()}

    for pk in ALL_PLATFORMS:
        result.setdefault(pk, {"approved": None, "status": "kein Urteil"})
    return result


def _match_platform(heading: str) -> str | None:
    for pk in ALL_PLATFORMS:
        name = spec(pk).name.lower()
        if name in heading or re.search(rf"\b{re.escape(pk)}\b", heading):
            return pk
    return None


def load_approvals(day_dir: Path) -> dict[str, dict]:
    """Lädt director_review.md aus dem Tages-Ordner und parst die Freigaben."""
    f = day_dir / "director_review.md"
    md = f.read_text(encoding="utf-8") if f.exists() else ""
    return parse_approvals(md)
