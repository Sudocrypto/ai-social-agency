"""Erzeugt einen editierbaren Start-Assembly-Plan aus einem Review-Paket.

Nimmt die generierten B-Roll-Clips + Untertitel aus dem Post-Production-Briefing
und baut ein assembly.json, das du von Hand feinjustierst (eigenes Material
einfügen, Timings anpassen, Musik-Datei setzen), bevor gerendert wird.
"""

from __future__ import annotations

import re
from pathlib import Path

from .plan import AssemblyPlan, Music, Segment

_SUB_BLOCK = re.compile(
    r"\*\*Untertitel-Text:\*\*\s*(.+?)(?:\n\*\*|\Z)", re.IGNORECASE | re.DOTALL
)


def extract_subtitles(post_production_md: str) -> list[str]:
    """Zieht den Untertitel-Text aus post_production.md und teilt ihn in Sätze."""
    m = _SUB_BLOCK.search(post_production_md or "")
    if not m:
        return []
    raw = re.sub(r"\s+", " ", m.group(1)).strip()
    # An Satzende splitten, Satzzeichen behalten.
    sentences = re.findall(r"[^.!?]+[.!?]?", raw)
    return [s.strip() for s in sentences if s.strip()]


def scaffold_plan(
    day_dir: Path, platform_key: str, *, clip_seconds: float = 5.0
) -> AssemblyPlan:
    """Baut einen Start-Plan: eigenes Auftakt-Material + generierte B-Roll + Untertitel."""
    pdir = day_dir / platform_key
    pp_file = pdir / "post_production.md"
    subs = extract_subtitles(pp_file.read_text(encoding="utf-8") if pp_file.exists() else "")

    broll = sorted((pdir / "broll").glob("*.mp4")) if (pdir / "broll").exists() else []

    segments: list[Segment] = []
    sub_iter = iter(subs)

    # 1) Auftakt aus eigenem Material (Platzhalter – du ersetzt den Pfad).
    segments.append(
        Segment(source="EIGENES_MATERIAL.mp4", start=0.0, end=clip_seconds,
                subtitle=next(sub_iter, ""), mute=False)
    )

    # 2) Generierte KI-B-Roll (stumm) – bzw. Platzhalter, falls nur Dry-Run-Prompts.
    if broll:
        for clip in broll:
            segments.append(
                Segment(source=str(clip), start=0.0, end=clip_seconds,
                        subtitle=next(sub_iter, ""), mute=True)
            )
    else:
        # Dry-Run: noch keine .mp4 – zwei Platzhalter mit den restlichen Untertiteln.
        for _ in range(2):
            segments.append(
                Segment(source="BROLL_PLATZHALTER.mp4", start=0.0, end=clip_seconds,
                        subtitle=next(sub_iter, ""), mute=True)
            )

    # Übrige Untertitel an das letzte Segment hängen, damit kein Text verloren geht.
    rest = " ".join(sub_iter)
    if rest and segments:
        tail = segments[-1].subtitle
        segments[-1].subtitle = (tail + " " + rest).strip() if tail else rest

    # YouTube = Querformat, sonst Hochformat (Reels/Shorts).
    if platform_key == "youtube":
        width, height = 1920, 1080
    else:
        width, height = 1080, 1920

    return AssemblyPlan(
        segments=segments,
        music=Music(source="MUSIK.mp3", gain_db=-18.0),
        width=width,
        height=height,
        fps=30,
        output="final.mp4",
    )


def single_clip_plan(
    clip_path: Path | str, *,
    seconds: float = 4.0, platform_key: str = "youtube", voice_path: Path | str | None = None,
) -> AssemblyPlan:
    """Render-Plan für EINEN Clip (freier Prompt-Test), optional mit Stimme als Tonspur."""
    width, height = (1920, 1080) if platform_key == "youtube" else (1080, 1920)
    seg = Segment(source=str(clip_path), start=0.0, end=seconds, subtitle="", mute=True)
    music = Music(source=str(voice_path), gain_db=0.0) if voice_path else None
    return AssemblyPlan(
        segments=[seg], music=music, width=width, height=height, fps=30, output="final.mp4",
    )


def auto_plan(
    day_dir: Path, platform_key: str, *,
    music: str | None = None, music_gain_db: float = -6.0, clip_seconds: float = 5.0,
) -> AssemblyPlan | None:
    """Baut einen render-fertigen Plan OHNE Platzhalter – für die Voll-Automatik.

    Nutzt ausschließlich die bereits gerenderten KI-B-Roll-Clips + die Untertitel
    aus dem Schnitt-Briefing. Gibt None zurück, wenn keine gerenderten .mp4-Clips
    vorliegen (dann kann nicht automatisch zusammengeschnitten werden).

    Da die KI-B-Roll stumm ist, ist die Musik die einzige Tonspur – deshalb per
    Default ein gut hörbarer Vordergrund-Pegel (-6 dB), nicht der Hintergrund-Wert.
    """
    pdir = day_dir / platform_key
    broll = sorted((pdir / "broll").glob("*.mp4")) if (pdir / "broll").exists() else []
    if not broll:
        return None

    pp_file = pdir / "post_production.md"
    subs = extract_subtitles(pp_file.read_text(encoding="utf-8") if pp_file.exists() else "")
    sub_iter = iter(subs)

    segments = [
        Segment(source=str(clip), start=0.0, end=clip_seconds,
                subtitle=next(sub_iter, ""), mute=True)
        for clip in broll
    ]
    rest = " ".join(sub_iter)
    if rest and segments:
        tail = segments[-1].subtitle
        segments[-1].subtitle = (tail + " " + rest).strip() if tail else rest

    width, height = (1920, 1080) if platform_key == "youtube" else (1080, 1920)
    return AssemblyPlan(
        segments=segments,
        music=Music(source=music, gain_db=music_gain_db) if music else None,
        width=width, height=height, fps=30, output="final.mp4",
    )
