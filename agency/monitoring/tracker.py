"""Tracker: hält fest, welche Videos wir veröffentlicht haben (für die Auswertung).

Speichert eine kleine JSON-Liste (video_id, url, titel, thema, added_at). Die
Datei liegt unter monitoring/ (gitignored) – enthält nur öffentliche Video-IDs.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from ..config import ROOT

DEFAULT_STORE = ROOT / "monitoring" / "tracking.json"

# 11-stellige YouTube-Video-ID.
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_URL_PATTERNS = [
    re.compile(r"(?:v=|/watch\?.*v=)([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"/shorts/([A-Za-z0-9_-]{11})"),
    re.compile(r"/embed/([A-Za-z0-9_-]{11})"),
]


def parse_video_id(url_or_id: str) -> str:
    """Extrahiert die YouTube-Video-ID aus einer URL oder akzeptiert eine rohe ID."""
    s = (url_or_id or "").strip()
    if _ID_RE.match(s):
        return s
    for rx in _URL_PATTERNS:
        m = rx.search(s)
        if m:
            return m.group(1)
    raise ValueError(f"Keine gültige YouTube-Video-ID/URL: {url_or_id!r}")


@dataclass
class TrackedVideo:
    video_id: str
    url: str
    titel: str = ""
    thema: str = ""
    added_at: str = field(default_factory=lambda: date.today().isoformat())


class Tracker:
    def __init__(self, store: Path | str = DEFAULT_STORE) -> None:
        self.store = Path(store)
        self.items: list[TrackedVideo] = []
        self._load()

    def _load(self) -> None:
        if self.store.exists():
            data = json.loads(self.store.read_text(encoding="utf-8"))
            self.items = [TrackedVideo(**d) for d in data]

    def save(self) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(
            json.dumps([asdict(i) for i in self.items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, url_or_id: str, *, titel: str = "", thema: str = "") -> TrackedVideo:
        vid = parse_video_id(url_or_id)
        if any(i.video_id == vid for i in self.items):
            raise ValueError(f"Video {vid} ist bereits getrackt.")
        url = url_or_id if url_or_id.startswith("http") else f"https://youtu.be/{vid}"
        item = TrackedVideo(video_id=vid, url=url, titel=titel, thema=thema)
        self.items.append(item)
        self.save()
        return item

    def video_ids(self) -> list[str]:
        return [i.video_id for i in self.items]

    def remove(self, url_or_id: str) -> bool:
        """Entfernt ein Video aus dem Tracking. True, wenn etwas entfernt wurde."""
        try:
            vid = parse_video_id(url_or_id)
        except ValueError:
            vid = url_or_id
        before = len(self.items)
        self.items = [i for i in self.items if i.video_id != vid]
        self.save()
        return len(self.items) < before

    def clear(self) -> int:
        """Leert das komplette Tracking. Gibt die Anzahl entfernter Einträge zurück."""
        n = len(self.items)
        self.items = []
        self.save()
        return n
