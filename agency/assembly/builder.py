"""Baut das ffmpeg-Kommando aus einem AssemblyPlan und rendert (lokal) die .mp4.

Video: Segmente trimmen -> auf Zielformat skalieren/padden -> aneinanderhängen
-> Untertitel einbrennen. Audio: Clip-Ton (oder Stille bei mute) aneinanderhängen
und Musik leiser darunter mischen.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .plan import AssemblyPlan
from .subtitles import build_srt, write_srt

SRT_NAME = ".assembly_subs.srt"


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _filtergraph(plan: AssemblyPlan, has_subs: bool) -> str:
    W, H, FPS = plan.width, plan.height, plan.fps
    parts: list[str] = []
    concat_inputs: list[str] = []

    for i, seg in enumerate(plan.segments):
        parts.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},"
            f"setpts=PTS-STARTPTS[v{i}]"
        )
        if seg.mute:
            parts.append(
                f"anullsrc=r=44100:cl=stereo,atrim=0:{seg.duration},"
                f"asetpts=PTS-STARTPTS[a{i}]"
            )
        else:
            parts.append(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}]")
        concat_inputs.append(f"[v{i}][a{i}]")

    n = len(plan.segments)
    parts.append("".join(concat_inputs) + f"concat=n={n}:v=1:a=1[vc][ac]")

    # Untertitel einbrennen (nur wenn vorhanden). Relativer Dateiname -> im
    # Arbeitsverzeichnis von ffmpeg; vermeidet Pfad-Escaping-Probleme.
    if has_subs:
        parts.append(f"[vc]subtitles={SRT_NAME}[vout]")
    else:
        parts.append("[vc]copy[vout]")

    music_idx = n  # Musik ist der letzte Input (falls vorhanden)
    if plan.music:
        parts.append(f"[{music_idx}:a]volume={plan.music.gain_db}dB[mvol]")
        parts.append("[ac][mvol]amix=inputs=2:duration=first:dropout_transition=0[aout]")
    else:
        parts.append("[ac]aresample=44100[aout]")

    return ";".join(parts)


def build_command(plan: AssemblyPlan, out_path: Path | str) -> list[str]:
    """Erzeugt das vollständige ffmpeg-Argument-Array (ohne es auszuführen)."""
    has_subs = bool(build_srt(plan).strip())
    args: list[str] = ["ffmpeg", "-y"]
    for seg in plan.segments:
        args += ["-ss", str(seg.start), "-t", str(seg.duration), "-i", seg.source]
    if plan.music:
        args += ["-i", plan.music.source]

    args += [
        "-filter_complex", _filtergraph(plan, has_subs),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-r", str(plan.fps),
        "-movflags", "+faststart",
        str(out_path),
    ]
    return args


def render(plan: AssemblyPlan, out_path: Path | str, *, dry_run: bool = True) -> dict:
    """Rendert das Video (oder simuliert im Dry-Run).

    Der ffmpeg-Aufruf läuft im Verzeichnis der Ausgabedatei, damit die relativ
    referenzierte Untertitel-Datei gefunden wird.
    """
    out_path = Path(out_path)
    errors = plan.validate()
    if errors:
        return {"ok": False, "rendered": False, "error": "; ".join(errors), "cmd": None}

    workdir = out_path.parent
    workdir.mkdir(parents=True, exist_ok=True)
    srt = build_srt(plan)
    if srt.strip():
        write_srt(plan, workdir / SRT_NAME)

    cmd = build_command(plan, out_path.name)  # out relativ zum workdir
    cmd_str = " ".join(cmd)

    if dry_run:
        return {
            "ok": True, "rendered": False, "cmd": cmd_str,
            "output": str(out_path), "duration_s": plan.total_duration,
            "note": "Dry-Run – nichts gerendert.",
        }

    if not ffmpeg_available():
        return {
            "ok": False, "rendered": False, "cmd": cmd_str,
            "error": "ffmpeg nicht gefunden. Bitte ffmpeg installieren.",
        }

    proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
    if proc.returncode != 0:
        return {
            "ok": False, "rendered": False, "cmd": cmd_str,
            "error": f"ffmpeg-Fehler (Code {proc.returncode}): {proc.stderr[-800:]}",
        }
    return {
        "ok": True, "rendered": True, "cmd": cmd_str,
        "output": str(out_path), "duration_s": plan.total_duration,
    }
