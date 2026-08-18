"""Einfache Post-Planung: welchem Paket/Plattform ist welcher Termin zugeordnet.

Speichert eine JSON-Liste (monitoring/schedule.json). Das Dashboard zeigt daraus
'Als Nächstes geplant'. Bewusst schlank: keine automatische Ausführung – ein
Termin ist eine Notiz/Erinnerung, gepostet wird bewusst per publish.py.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import ROOT
from .platforms import PLATFORMS

SCHEDULE = ROOT / "monitoring" / "schedule.json"


def parse_when(s: str) -> str:
    """Akzeptiert 'YYYY-MM-DD HH:MM' oder ISO und gibt ISO (bis Minute) zurück."""
    s = (s or "").strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.isoformat(timespec="minutes")
        except ValueError:
            continue
    raise ValueError(f"Ungültiger Zeitpunkt: {s!r}. Format: 'YYYY-MM-DD HH:MM'.")


def load_schedule(store: Path | str = SCHEDULE) -> list[dict]:
    p = Path(store)
    if not p.exists():
        return []
    entries = json.loads(p.read_text(encoding="utf-8"))
    return sorted(entries, key=lambda e: e.get("at", ""))


def add_entry(
    package_date: str, platform: str, when: str,
    *, note: str = "", store: Path | str = SCHEDULE,
) -> dict:
    if platform not in PLATFORMS:
        raise ValueError(f"Unbekannte Plattform '{platform}'. Erlaubt: {', '.join(PLATFORMS)}")
    entry = {
        "package_date": package_date,
        "platform": platform,
        "at": parse_when(when),
        "note": note,
    }
    entries = load_schedule(store)
    entries.append(entry)
    p = Path(store)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def remove_entry(index: int, store: Path | str = SCHEDULE) -> bool:
    entries = load_schedule(store)
    if not (0 <= index < len(entries)):
        return False
    entries.pop(index)
    Path(store).write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return True
