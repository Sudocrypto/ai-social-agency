"""Baut das ffmpeg-Kommando aus einem AssemblyPlan und rendert (lokal) die .mp4.

Video: Segmente trimmen -> auf Zielformat skalieren/padden -> aneinanderhängen
-> Untertitel einbrennen. Audio: Clip-Ton (oder Stille bei mute) aneinanderhängen
und Musik leiser darunter mischen.
"""

from __future__ import annotations

import functools
import shutil
import subprocess
from pathlib import Path

from .plan import AssemblyPlan
from .subtitles import build_srt, write_srt

# Kein führender Punkt: ffmpeg deutet ".name" im subtitles-Filter sonst als
# fehlende Option ("No option name near '.assembly_subs.srt'").
SRT_NAME = "assembly_subs.srt"

# Standbilder werden zu einem Clip "geloopt" (anderes ffmpeg-Input-Handling als Video).
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".heic"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}


def is_image(source: str) -> bool:
    return Path(source).suffix.lower() in IMAGE_EXTS


def is_media(source: str) -> bool:
    return Path(source).suffix.lower() in (IMAGE_EXTS | VIDEO_EXTS)


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@functools.lru_cache(maxsize=1)
def subtitles_supported() -> bool:
    """Ob dieses ffmpeg den 'subtitles'-Filter (libass) hat.

    Manche Builds (z. B. bestimmte Homebrew-Varianten) kommen ohne libass –
    dann fehlt der subtitles-Filter und Untertitel können nicht eingebrannt
    werden. Ergebnis wird gecacht.
    """
    if not ffmpeg_available():
        return False
    try:
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-filters"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return False
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "subtitles":
            return True
    return False


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
        # Dateiname EXPLIZIT als filename= – ffmpeg 8.x akzeptiert ihn nicht
        # positional ("No option name near 'assembly_subs.srt'").
        parts.append(f"[vc]subtitles=filename={SRT_NAME}[vout]")
    else:
        parts.append("[vc]copy[vout]")

    music_idx = n  # Musik ist der letzte Input (falls vorhanden)
    if plan.music:
        parts.append(f"[{music_idx}:a]volume={plan.music.gain_db}dB[mvol]")
        parts.append("[ac][mvol]amix=inputs=2:duration=first:dropout_transition=0[aout]")
    else:
        parts.append("[ac]aresample=44100[aout]")

    return ";".join(parts)


def build_command(
    plan: AssemblyPlan, out_path: Path | str, *, burn_subtitles: bool = True
) -> list[str]:
    """Erzeugt das vollständige ffmpeg-Argument-Array (ohne es auszuführen)."""
    has_subs = burn_subtitles and bool(build_srt(plan).strip())
    args: list[str] = ["ffmpeg", "-y"]
    for seg in plan.segments:
        if is_image(seg.source):
            # Standbild -> N Sekunden Video: -loop 1 + -t Dauer.
            args += ["-loop", "1", "-t", str(seg.duration), "-i", seg.source]
        else:
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


def _animated_image_chain(idx: int, dur: float, W: int, H: int, FPS: int) -> str:
    """Ken-Burns-Zoom für ein Standbild. `trim` kappt die Überproduktion von zoompan."""
    frames = max(1, int(round(dur * FPS)))
    return (
        f"[{idx}:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
        f"crop={W*2}:{H*2},"
        f"zoompan=z='min(zoom+0.0015,1.5)':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
        f"trim=duration={dur},setsar=1,setpts=PTS-STARTPTS[v{idx}]"
    )


def _static_scale_chain(idx: int, W: int, H: int, FPS: int) -> str:
    return (
        f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},setpts=PTS-STARTPTS[v{idx}]"
    )


def build_crossfade_command(
    plan: AssemblyPlan, out_path: Path | str, *, xfade: float = 1.0, transition: str = "fade",
) -> list[str]:
    """ffmpeg-Kommando: Segmente per Crossfade überblenden, Fotos sanft zoomen.

    Fotos animiert (Ken Burns), Videos normal skaliert; aufeinanderfolgende
    Segmente werden per xfade weich überblendet. Ton = Stimme/Musik (Clip-Ton
    entfällt in diesem Modus), sonst Stille. Keine Untertitel.
    """
    W, H, FPS = plan.width, plan.height, plan.fps
    segs = plan.segments
    n = len(segs)

    args: list[str] = ["ffmpeg", "-y"]
    for seg in segs:
        if is_image(seg.source):
            args += ["-loop", "1", "-t", str(seg.duration), "-i", seg.source]
        else:
            args += ["-ss", str(seg.start), "-t", str(seg.duration), "-i", seg.source]
    if plan.music:
        args += ["-i", plan.music.source]

    parts: list[str] = []
    for i, seg in enumerate(segs):
        if is_image(seg.source):
            parts.append(_animated_image_chain(i, seg.duration, W, H, FPS))
        else:
            parts.append(_static_scale_chain(i, W, H, FPS))

    # xfade-Kette + Gesamtdauer.
    if n == 1:
        parts.append("[v0]copy[vout]")
        total = segs[0].duration
    else:
        prev, cum = "v0", segs[0].duration
        for i in range(1, n):
            off = round(cum - xfade, 3)
            out = "vout" if i == n - 1 else f"vx{i}"
            parts.append(
                f"[{prev}][v{i}]xfade=transition={transition}:duration={xfade}:offset={off}[{out}]"
            )
            cum = round(cum + segs[i].duration - xfade, 3)
            prev = out
        total = cum

    music_idx = n
    if plan.music:
        parts.append(
            f"[{music_idx}:a]atrim=0:{total},asetpts=PTS-STARTPTS,"
            f"volume={plan.music.gain_db}dB[aout]"
        )
    else:
        parts.append(f"anullsrc=r=44100:cl=stereo,atrim=0:{total}[aout]")

    args += [
        "-filter_complex", ";".join(parts),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-r", str(FPS),
        "-movflags", "+faststart",
        str(out_path),
    ]
    return args


def render(
    plan: AssemblyPlan, out_path: Path | str, *,
    dry_run: bool = True, crossfade: bool = False, xfade: float = 1.0,
) -> dict:
    """Rendert das Video (oder simuliert im Dry-Run).

    Der ffmpeg-Aufruf läuft im Verzeichnis der Ausgabedatei, damit die relativ
    referenzierte Untertitel-Datei gefunden wird. Mit crossfade=True werden
    Segmente überblendet (Fotos animiert) statt hart aneinandergehängt.
    """
    out_path = Path(out_path)
    errors = plan.validate()
    if errors:
        return {"ok": False, "rendered": False, "error": "; ".join(errors), "cmd": None}

    workdir = out_path.parent
    workdir.mkdir(parents=True, exist_ok=True)

    # Crossfade-Modus: eigener Kommandobau, keine Untertitel.
    if crossfade:
        total = round(sum(s.duration for s in plan.segments) - max(0, len(plan.segments) - 1) * xfade, 3)
        cmd = build_crossfade_command(plan, out_path.name, xfade=xfade)
        cmd_str = " ".join(cmd)
        if dry_run:
            return {"ok": True, "rendered": False, "cmd": cmd_str,
                    "output": str(out_path), "duration_s": total, "warning": None}
        if not ffmpeg_available():
            return {"ok": False, "rendered": False, "cmd": cmd_str,
                    "error": "ffmpeg nicht gefunden. Bitte ffmpeg installieren."}
        proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
        if proc.returncode != 0:
            return {"ok": False, "rendered": False, "cmd": cmd_str,
                    "error": f"ffmpeg-Fehler (Code {proc.returncode}): {proc.stderr[-800:]}"}
        return {"ok": True, "rendered": True, "cmd": cmd_str,
                "output": str(out_path), "duration_s": total, "warning": None}

    srt = build_srt(plan)
    want_subs = bool(srt.strip())

    # Beim echten Rendern nur einbrennen, wenn dieses ffmpeg den subtitles-Filter
    # (libass) hat – sonst Untertitel überspringen statt komplett abzubrechen.
    burn_subs = want_subs if dry_run else (want_subs and subtitles_supported())
    warning = None
    if want_subs and not burn_subs and not dry_run:
        warning = ("ffmpeg ohne libass → Untertitel werden NICHT eingebrannt. "
                   "Für Untertitel: ffmpeg mit libass installieren "
                   "(brew reinstall ffmpeg).")
    if burn_subs:
        write_srt(plan, workdir / SRT_NAME)

    cmd = build_command(plan, out_path.name, burn_subtitles=burn_subs)  # out relativ zum workdir
    cmd_str = " ".join(cmd)

    if dry_run:
        return {
            "ok": True, "rendered": False, "cmd": cmd_str,
            "output": str(out_path), "duration_s": plan.total_duration,
            "note": "Dry-Run – nichts gerendert.", "warning": warning,
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
        "warning": warning,
    }
