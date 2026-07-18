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

    Drei Stufen des Directors:
      ✅ FREIGABE                -> approved=True,  tier="freigabe"
      🟡 FREIGABE MIT HINWEISEN  -> approved=True,  tier="hinweise" (postbar, Tipps fürs
                                    nächste Mal – blockiert NICHT)
      ⚠️ NACHBESSERN             -> approved=False, tier="nachbessern" (echter Blocker)

    Rückgabe: {platform_key: {"approved": bool | None, "status": str, "tier": str}}
    approved ist None, wenn kein Urteil vorliegt.
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
                result[current] = {"approved": False, "status": line.strip(), "tier": "nachbessern"}
            elif "HINWEISEN" in up or "🟡" in line:
                # "FREIGABE MIT HINWEISEN" – postbar, blockiert nicht.
                result[current] = {"approved": True, "status": line.strip(), "tier": "hinweise"}
            elif "FREIGABE" in up or "✅" in line:
                result[current] = {"approved": True, "status": line.strip(), "tier": "freigabe"}

    for pk in ALL_PLATFORMS:
        result.setdefault(pk, {"approved": None, "status": "kein Urteil", "tier": None})
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


def parse_compliance(report_md: str) -> dict[str, dict]:
    """Ordnet jeder Plattform das Compliance-Verdikt zu.

    Rückgabe: {platform_key: {"ok": bool | None, "status": str}}
    ok=False bei RISIKO, True bei OK, None wenn keine Prüfung vorliegt.
    """
    result: dict[str, dict] = {}
    current: str | None = None

    for line in (report_md or "").splitlines():
        m = _HEADING.match(line)
        if m:
            current = _match_platform(m.group(1).strip().lower())
            continue
        if current and current not in result:
            up = line.upper()
            if "RISIKO" in up:
                result[current] = {"ok": False, "status": line.strip()}
            elif "✅" in line or re.search(r"\bOK\b", up):
                result[current] = {"ok": True, "status": line.strip()}

    for pk in ALL_PLATFORMS:
        result.setdefault(pk, {"ok": None, "status": "keine Prüfung"})
    return result


def load_compliance(day_dir: Path) -> dict[str, dict]:
    """Lädt compliance_report.md aus dem Tages-Ordner und parst die Verdikte."""
    f = day_dir / "compliance_report.md"
    md = f.read_text(encoding="utf-8") if f.exists() else ""
    return parse_compliance(md)


def gate_status(day_dir: Path, platform: str) -> dict:
    """Kombiniertes Freigabe-Gate für die Automatik.

    allowed=False, sobald der Director NACHBESSERN oder die Compliance RISIKO meldet.
    """
    approval = load_approvals(day_dir).get(platform, {})
    director = approval.get("approved")
    tier = approval.get("tier")
    compliance = load_compliance(day_dir).get(platform, {}).get("ok")
    if director is False:
        reason = "Creative Director: NACHBESSERN"
    elif compliance is False:
        reason = "Compliance-Prüfer: RISIKO"
    elif tier == "hinweise":
        reason = "frei (Director: mit Hinweisen)"
    else:
        reason = "frei"
    return {
        "director": director,
        "tier": tier,
        "compliance": compliance,
        "allowed": director is not False and compliance is not False,
        "reason": reason,
    }
