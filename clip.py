#!/usr/bin/env python3
"""Rendert EINEN KI-Clip aus einem freien Prompt (+ optionale Stimme) zu einem MP4.

Für schnelle Einzeltests, unabhängig von der Themen-Pipeline. Kostet fal.ai-
Guthaben (ein Clip), nur bei erfolgreichem Render.

    python clip.py --config brand_config.ki.yaml --prompt "…" --seconds 4
    python clip.py --config brand_config.ki.yaml --prompt "…" \
        --voice "…" --voice-engine fal

Hinweis: Keine markenrechtlich geschützten Figuren/Logos in den Prompt (z. B.
statt "Spider-Man" -> "maskierter Superheld im roten Anzug an Netzen").
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from agency.assembly.builder import ffmpeg_available, render
from agency.assembly.scaffold import clips_plan
from agency.assembly.voiceover import synthesize
from agency.config import ROOT, load_config
from agency.platforms import ALL_PLATFORMS
from agency.video import fal_client


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Freie KI-Clips rendern (+ optional Stimme).")
    p.add_argument("--prompt", required=True, action="append",
                   help="Bildbeschreibung. Mehrfach angeben -> mehrere Szenen nacheinander.")
    p.add_argument("--seconds", type=int, default=4, help="Länge PRO Clip (fal-Minimum 4).")
    p.add_argument("--platform", default="youtube", choices=ALL_PLATFORMS)
    p.add_argument("--config", default=None)
    p.add_argument("--voice", default=None, help="Optionaler Text, der gesprochen wird.")
    p.add_argument("--voice-engine", default="say", choices=["say", "fal"])
    p.add_argument("--voice-name", default=None)
    p.add_argument("--out", default=None, help="Ausgabeordner (Default: output/clip-<zeit>).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config(args.config) if args.config else load_config()
    if not cfg.fal_key:
        print("FEHLER: FAL_KEY fehlt in .env – ohne den kann kein Clip gerendert werden.",
              file=sys.stderr)
        return 2

    model = cfg.video.get("video_modell", "veo-3.1")
    secs = max(4, args.seconds)
    prompts = args.prompt
    est = fal_client.estimate_cost_eur(model, secs) * len(prompts)
    outdir = Path(args.out) if args.out else (ROOT / "output" / f"clip-{time.strftime('%Y%m%d-%H%M%S')}")
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"🎬 Rendere {len(prompts)} Szene(n) à {secs}s ({model}) … geschätzt ~{est:.2f} €")
    clip_paths: list[Path] = []
    for i, prompt in enumerate(prompts, 1):
        print(f"   [{i}/{len(prompts)}] {prompt[:60]}…")
        try:
            data = fal_client.render_clip(
                prompt=prompt, seconds=secs, model=model, api_key=cfg.fal_key
            )
        except Exception as exc:
            # Abgelehnte Szene (z. B. Content-Filter) kostet nichts – überspringen.
            print(f"      ⚠️  Szene {i} übersprungen: {exc}", file=sys.stderr)
            continue
        clip_path = outdir / f"clip_{i:02d}.mp4"
        clip_path.write_bytes(data)
        clip_paths.append(clip_path)
        print(f"      ✓ gespeichert: {clip_path.name}")

    if not clip_paths:
        print("❌ Keine Szene wurde gerendert (alle abgelehnt/fehlgeschlagen).", file=sys.stderr)
        return 1

    voice_path: Path | None = None
    if args.voice:
        suffix = "aiff" if args.voice_engine == "say" else "mp3"
        voice_path = outdir / f"voiceover.{suffix}"
        try:
            synthesize(args.voice, voice_path, engine=args.voice_engine,
                       voice=args.voice_name, api_key=cfg.fal_key)
        except Exception as exc:
            print(f"❌ Stimme fehlgeschlagen: {exc}", file=sys.stderr)
            return 1
        print(f"🎙  Stimme erzeugt: {voice_path}")

    plan = clips_plan(clip_paths, seconds=secs, platform_key=args.platform,
                      voice_path=voice_path)
    final = outdir / plan.output
    if not ffmpeg_available():
        print(f"⏹  ffmpeg fehlt – der rohe Clip liegt unter {clip_path}.")
        return 0
    res = render(plan, final, dry_run=False)
    if res.get("warning"):
        print(f"⚠️  {res['warning']}")
    if not res["ok"]:
        print(f"❌ Render-Fehler: {res.get('error')}", file=sys.stderr)
        return 1
    print(f"✅ Fertig: {final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
