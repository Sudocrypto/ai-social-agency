#!/usr/bin/env python3
"""Baut aus DEINEM eigenen Material (Fotos + Videos) ein Video – optional mit Stimme/Musik.

Kostet KEIN fal.ai-Geld (nur ffmpeg), außer du nutzt --voice-engine fal.
Reihenfolge = Reihenfolge der --media-Angaben. Fotos werden zu kurzen Clips.

    python mymedia.py --media clip1.mov --media foto.jpg --media clip2.mp4 --seconds 4
    python mymedia.py --media a.jpg --media b.jpg --voice "Mein Text" --voice-engine fal
    python mymedia.py --media a.mp4 --music ~/Downloads/song.mp3
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from agency.assembly.builder import ffmpeg_available, is_media, render
from agency.assembly.scaffold import media_plan
from agency.assembly.voiceover import synthesize
from agency.config import ROOT, load_config
from agency.platforms import ALL_PLATFORMS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Video aus eigenen Fotos/Videos bauen.")
    p.add_argument("--media", action="append", default=None,
                   help="Pfad zu Foto/Video. Mehrfach angeben -> Reihenfolge im Video.")
    p.add_argument("--folder", default=None,
                   help="Ordner mit Fotos/Videos – alle darin (alphabetisch) werden genutzt.")
    p.add_argument("--seconds", type=int, default=4, help="Dauer pro Foto/Clip-Abschnitt.")
    p.add_argument("--platform", default="youtube", choices=ALL_PLATFORMS)
    p.add_argument("--config", default=None)
    p.add_argument("--voice", default=None, help="Optionaler gesprochener Text (Tonspur).")
    p.add_argument("--voice-engine", default="say", choices=["say", "fal"])
    p.add_argument("--voice-name", default=None)
    p.add_argument("--music", default=None, help="Optionale Musikdatei (statt Stimme).")
    p.add_argument("--music-gain", type=float, default=-6.0, help="Musik-Pegel in dB.")
    p.add_argument("--crossfade", action="store_true",
                   help="Segmente weich überblenden (Fotos animiert/Ken-Burns) statt hart schneiden.")
    p.add_argument("--xfade-seconds", type=float, default=1.0,
                   help="Dauer der Überblendung in Sekunden (nur mit --crossfade).")
    p.add_argument("--out", default=None, help="Ausgabeordner (Default: output/mymedia-<zeit>).")
    p.add_argument("--render", action="store_true", help="Echt rendern statt Dry-Run.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Quellen sammeln: einzelne --media und/oder alle Dateien aus --folder.
    media: list[str] = []
    if args.folder:
        folder = Path(args.folder).expanduser()
        if not folder.is_dir():
            print(f"FEHLER: Ordner nicht gefunden: {folder}", file=sys.stderr)
            return 2
        found = sorted(p for p in folder.iterdir() if p.is_file() and is_media(p.name))
        if not found:
            print(f"FEHLER: Keine Fotos/Videos in {folder} gefunden.", file=sys.stderr)
            return 2
        media += [str(p) for p in found]
    if args.media:
        missing = [m for m in args.media if not Path(m).expanduser().exists()]
        if missing:
            print("FEHLER: Diese Dateien wurden nicht gefunden:", file=sys.stderr)
            for m in missing:
                print(f"  - {m}", file=sys.stderr)
            return 2
        media += [str(Path(m).expanduser()) for m in args.media]

    if not media:
        print("FEHLER: Gib --media <datei> (mehrfach) oder --folder <ordner> an.", file=sys.stderr)
        return 2
    print(f"📂 {len(media)} Datei(en):")
    for m in media:
        print(f"   - {Path(m).name}")

    outdir = Path(args.out) if args.out else (ROOT / "output" / f"mymedia-{time.strftime('%Y%m%d-%H%M%S')}")
    outdir.mkdir(parents=True, exist_ok=True)

    voice_path: Path | None = None
    if args.voice:
        cfg = load_config(args.config) if args.config else load_config()
        fal_key = cfg.fal_key if args.voice_engine == "fal" else None
        suffix = "aiff" if args.voice_engine == "say" else "mp3"
        voice_path = outdir / f"voiceover.{suffix}"
        try:
            synthesize(args.voice, voice_path, engine=args.voice_engine,
                       voice=args.voice_name, api_key=fal_key)
        except Exception as exc:
            print(f"❌ Stimme fehlgeschlagen: {exc}", file=sys.stderr)
            return 1
        print(f"🎙  Stimme erzeugt: {voice_path}")

    plan = media_plan(
        media, seconds=max(1, args.seconds), platform_key=args.platform,
        voice_path=voice_path, music_path=args.music, music_gain_db=args.music_gain,
    )
    final = outdir / plan.output
    # Überblendung darf nicht länger sein als das kürzeste Segment.
    xfade = min(args.xfade_seconds, max(0.2, args.seconds * 0.8))
    result = render(plan, final, dry_run=not args.render,
                    crossfade=args.crossfade, xfade=xfade)

    if result.get("warning"):
        print(f"⚠️  {result['warning']}")
    if not result["ok"]:
        print(f"❌ {result.get('error')}", file=sys.stderr)
        if result.get("cmd"):
            print(f"\nffmpeg-Kommando:\n{result['cmd']}")
        return 1
    if result["rendered"]:
        print(f"✅ Video gerendert: {result['output']} (~{result['duration_s']}s)")
    else:
        print(f"🔍 Dry-Run – Gesamtlänge ~{result['duration_s']}s. Mit --render wirklich bauen.")
        if not ffmpeg_available():
            print("ℹ️  ffmpeg ist hier nicht installiert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
