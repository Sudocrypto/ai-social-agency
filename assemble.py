#!/usr/bin/env python3
"""Video-Assembly-CLI: baut aus dem Schnittplan eine fertige .mp4 (via ffmpeg).

Ablauf:
  1. Erststart legt ein editierbares assembly.json an (aus B-Roll + Untertiteln).
     Du trägst dein eigenes Material, Timings und die Musikdatei ein.
  2. Zweiter Aufruf: Dry-Run zeigt das ffmpeg-Kommando + schreibt die Untertitel.
  3. Mit --render wird tatsächlich gerendert (ffmpeg muss installiert sein).

Beispiele:
    python assemble.py --platform youtube                 # scaffolded / Dry-Run
    python assemble.py --platform instagram --scaffold     # assembly.json neu erzeugen
    python assemble.py --platform youtube --render         # echt rendern
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agency.assembly.builder import ffmpeg_available, render
from agency.assembly.plan import AssemblyPlan
from agency.assembly.scaffold import scaffold_plan
from agency.config import ROOT
from agency.platforms import ALL_PLATFORMS

OUTPUT_ROOT = ROOT / "output"


def _latest_day() -> Path | None:
    if not OUTPUT_ROOT.exists():
        return None
    days = sorted((p for p in OUTPUT_ROOT.iterdir() if p.is_dir()), reverse=True)
    return days[0] if days else None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Baut das finale Video aus dem Schnittplan.")
    p.add_argument("--platform", required=True, choices=ALL_PLATFORMS)
    p.add_argument("--date", default=None, help="Paket-Datum (YYYY-MM-DD). Default: neuestes.")
    p.add_argument("--out", default=None, help="Ausgabepfad (Default: <plattform>/final.mp4).")
    p.add_argument("--scaffold", action="store_true",
                   help="assembly.json (neu) aus dem Paket erzeugen und beenden.")
    p.add_argument("--render", action="store_true",
                   help="Echt rendern statt Dry-Run (braucht ffmpeg + echte Dateien).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    day_dir = (OUTPUT_ROOT / args.date) if args.date else _latest_day()
    if not day_dir or not day_dir.exists():
        print("FEHLER: Kein Review-Paket gefunden. Erst 'python run.py …' ausführen.",
              file=sys.stderr)
        return 2

    pdir = day_dir / args.platform
    plan_path = pdir / "assembly.json"

    # Scaffolding: bei --scaffold oder wenn noch kein Plan existiert.
    if args.scaffold or not plan_path.exists():
        pdir.mkdir(parents=True, exist_ok=True)
        plan = scaffold_plan(day_dir, args.platform)
        plan.save(plan_path)
        print(f"📝 Schnittplan angelegt: {plan_path}")
        print("   Bitte editieren: eigene Clip-Pfade, Timings (start/end), "
              "Untertitel und MUSIK.mp3 eintragen.")
        print("   Danach erneut ausführen (Dry-Run), dann mit --render rendern.")
        return 0

    plan = AssemblyPlan.load(plan_path)
    out_path = Path(args.out) if args.out else (pdir / plan.output)

    result = render(plan, out_path, dry_run=not args.render)

    if not result["ok"]:
        print(f"❌ {result.get('error')}", file=sys.stderr)
        if result.get("cmd"):
            print(f"\nffmpeg-Kommando:\n{result['cmd']}")
        return 1

    if result["rendered"]:
        print(f"✅ Video gerendert: {result['output']} (~{result['duration_s']}s)")
    else:
        print(f"🔍 Dry-Run – Gesamtlänge ~{result['duration_s']}s. Nichts gerendert.")
        print(f"   Ausgabeziel wäre: {result['output']}")
        print(f"\nffmpeg-Kommando:\n{result['cmd']}")
        if not ffmpeg_available():
            print("\nℹ️  ffmpeg ist hier nicht installiert – zum echten Rendern lokal "
                  "ffmpeg installieren und --render nutzen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
