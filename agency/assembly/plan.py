"""Assembly-Plan: strukturierte, editierbare Beschreibung des finalen Videos.

Bewusst als JSON-Datei (assembly.json) angelegt, damit du den Schnitt von Hand
feinjustieren kannst, bevor gerendert wird.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Segment:
    """Ein Clip im finalen Video.

    `source` = Pfad zur Videodatei (dein Material ODER KI-B-Roll).
    Getrimmt auf [start, end] Sekunden. `mute=True` verwirft die Tonspur des
    Clips (z.B. stummer KI-B-Roll) – dafür wird Stille eingesetzt.
    `subtitle` = eingebrannter Untertiteltext für dieses Segment.
    """

    source: str
    start: float = 0.0
    end: float = 5.0
    subtitle: str = ""
    mute: bool = False

    @property
    def duration(self) -> float:
        return round(max(0.0, self.end - self.start), 3)


@dataclass
class Music:
    source: str
    gain_db: float = -18.0  # Hintergrund-Pegel (leiser als Sprache)


@dataclass
class AssemblyPlan:
    segments: list[Segment] = field(default_factory=list)
    music: Music | None = None
    width: int = 1080
    height: int = 1920      # 9:16 (Reels/Shorts); für YouTube-Langform 1920x1080 setzen
    fps: int = 30
    output: str = "final.mp4"

    @property
    def total_duration(self) -> float:
        return round(sum(s.duration for s in self.segments), 3)

    # --- Validierung ---------------------------------------------------------
    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.segments:
            errors.append("Keine Segmente im Plan.")
        for i, s in enumerate(self.segments, 1):
            if s.duration <= 0:
                errors.append(f"Segment {i}: end ({s.end}) muss > start ({s.start}) sein.")
            if not s.source:
                errors.append(f"Segment {i}: kein source-Pfad.")
        if self.width <= 0 or self.height <= 0 or self.fps <= 0:
            errors.append("width/height/fps müssen > 0 sein.")
        return errors

    # --- (De)Serialisierung --------------------------------------------------
    def to_dict(self) -> dict:
        d = asdict(self)
        if self.music is None:
            d["music"] = None
        return d

    def save(self, path: Path | str) -> Path:
        path = Path(path)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    @classmethod
    def from_dict(cls, data: dict) -> "AssemblyPlan":
        segments = [Segment(**s) for s in data.get("segments", [])]
        music_raw = data.get("music")
        music = Music(**music_raw) if music_raw else None
        return cls(
            segments=segments,
            music=music,
            width=data.get("width", 1080),
            height=data.get("height", 1920),
            fps=data.get("fps", 30),
            output=data.get("output", "final.mp4"),
        )

    @classmethod
    def load(cls, path: Path | str) -> "AssemblyPlan":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
