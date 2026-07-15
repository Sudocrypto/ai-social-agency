"""Erzeugt eine SRT-Untertiteldatei aus den Segment-Texten + Timings."""

from __future__ import annotations

from pathlib import Path

from .plan import AssemblyPlan


def _ts(seconds: float) -> str:
    """Sekunden -> SRT-Zeitstempel HH:MM:SS,mmm."""
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(plan: AssemblyPlan) -> str:
    """Baut den SRT-Inhalt: pro Segment mit Text ein Cue über dessen Zeitfenster."""
    cues: list[str] = []
    clock = 0.0
    n = 0
    for seg in plan.segments:
        dur = seg.duration
        text = (seg.subtitle or "").strip()
        if text:
            n += 1
            cues.append(
                f"{n}\n{_ts(clock)} --> {_ts(clock + dur)}\n{text}\n"
            )
        clock += dur
    return "\n".join(cues)


def write_srt(plan: AssemblyPlan, path: Path | str) -> Path:
    path = Path(path)
    path.write_text(build_srt(plan), encoding="utf-8")
    return path
