#!/usr/bin/env python3
"""Monitoring-CLI: verfolgt, wie gut veröffentlichte Videos ankommen.

Ablauf:
  1. Nach dem Hochladen die Video-URL tracken:
        python monitor.py add "https://youtu.be/XXXXXXXXXXX" --thema "Bitcoin ETF"
  2. Später Performance abrufen (braucht YOUTUBE_API_KEY in .env):
        python monitor.py fetch
     -> schreibt monitoring/report.md + monitoring/metrics.csv
  3. Die Metriken in den Growth-Analysten füttern:
        python run.py --config brand_config.crypto.yaml --pillar news \\
            --platform youtube --metrics monitoring/metrics.csv

    python monitor.py list        # getrackte Videos anzeigen
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agency.config import ROOT
from agency.monitoring.report import build_report, to_metrics_csv
from agency.monitoring.tracker import Tracker
from agency.monitoring.youtube_stats import fetch_stats

MON_DIR = ROOT / "monitoring"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Überwacht die Performance veröffentlichter Videos.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Ein veröffentlichtes Video zum Tracking hinzufügen.")
    a.add_argument("url", help="YouTube-URL oder Video-ID.")
    a.add_argument("--titel", default="", help="Optionaler Titel/Notiz.")
    a.add_argument("--thema", default="", help="Optionales Thema/Kampagne.")

    sub.add_parser("list", help="Getrackte Videos anzeigen.")

    r = sub.add_parser("remove", help="Ein Video aus dem Tracking entfernen.")
    r.add_argument("url", help="YouTube-URL oder Video-ID.")

    sub.add_parser("clear", help="Gesamtes Tracking leeren.")

    f = sub.add_parser("fetch", help="Stats abrufen + Report/CSV schreiben.")
    f.add_argument("--out", default=str(MON_DIR / "report.md"))
    f.add_argument("--csv", default=str(MON_DIR / "metrics.csv"))
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tracker = Tracker()

    if args.cmd == "add":
        try:
            item = tracker.add(args.url, titel=args.titel, thema=args.thema)
        except ValueError as exc:
            print(f"FEHLER: {exc}", file=sys.stderr)
            return 2
        print(f"✅ getrackt: {item.video_id} ({item.url})")
        return 0

    if args.cmd == "list":
        if not tracker.items:
            print("Noch keine Videos getrackt. 'python monitor.py add <url>' benutzen.")
            return 0
        for i in tracker.items:
            print(f"- {i.video_id}  {i.thema or '—'}  ({i.added_at})  {i.url}")
        return 0

    if args.cmd == "remove":
        removed = tracker.remove(args.url)
        print("✅ entfernt." if removed else "Nichts entfernt (nicht getrackt).")
        return 0 if removed else 1

    if args.cmd == "clear":
        n = tracker.clear()
        print(f"✅ Tracking geleert ({n} Einträge entfernt).")
        return 0

    if args.cmd == "fetch":
        if not tracker.video_ids():
            print("Keine getrackten Videos. Erst 'python monitor.py add <url>'.", file=sys.stderr)
            return 2
        load_dotenv(ROOT / ".env")
        api_key = os.environ.get("YOUTUBE_API_KEY")
        try:
            stats = fetch_stats(tracker.video_ids(), api_key)
        except Exception as exc:
            print(f"FEHLER beim Abruf: {exc}", file=sys.stderr)
            return 1

        MON_DIR.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(build_report(stats), encoding="utf-8")
        Path(args.csv).write_text(to_metrics_csv(stats), encoding="utf-8")
        total = sum(s["views"] for s in stats)
        print(f"✅ {len(stats)} Video(s) ausgewertet · {total} Views gesamt")
        print(f"   Report: {args.out}")
        print(f"   Metriken (für --metrics): {args.csv}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
