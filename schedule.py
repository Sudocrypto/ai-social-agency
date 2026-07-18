#!/usr/bin/env python3
"""Planungs-CLI: ordnet einem Paket/Plattform einen geplanten Post-Termin zu.

Erscheint im Dashboard unter 'Als Nächstes geplant'. Es wird NICHT automatisch
gepostet – der Termin ist eine Erinnerung; posten machst du bewusst per publish.py.

    python schedule.py add 2026-07-20 youtube "2026-07-20 09:00" --note "Bitcoin ETF"
    python schedule.py list
    python schedule.py remove 0
"""

from __future__ import annotations

import argparse
import sys

from agency.platforms import ALL_PLATFORMS
from agency.scheduling import add_entry, load_schedule, remove_entry


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Plant Post-Termine für Pakete/Plattformen.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Einen Termin anlegen.")
    a.add_argument("package_date", help="Paket-Datum (Ordner in output/, z.B. 2026-07-20).")
    a.add_argument("platform", choices=ALL_PLATFORMS)
    a.add_argument("when", help="Zeitpunkt 'YYYY-MM-DD HH:MM'.")
    a.add_argument("--note", default="", help="Optionale Notiz.")

    sub.add_parser("list", help="Geplante Termine anzeigen.")

    r = sub.add_parser("remove", help="Einen Termin per Index entfernen (siehe list).")
    r.add_argument("index", type=int)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "add":
        try:
            e = add_entry(args.package_date, args.platform, args.when, note=args.note)
        except ValueError as exc:
            print(f"FEHLER: {exc}", file=sys.stderr)
            return 2
        print(f"✅ geplant: {e['platform']} am {e['at']} (Paket {e['package_date']})")
        return 0

    if args.cmd == "list":
        entries = load_schedule()
        if not entries:
            print("Keine Termine geplant. 'python schedule.py add <paket> <plattform> <zeit>'.")
            return 0
        for i, e in enumerate(entries):
            note = f" – {e['note']}" if e.get("note") else ""
            print(f"[{i}] {e['at']}  {e['platform']}  (Paket {e['package_date']}){note}")
        return 0

    if args.cmd == "remove":
        ok = remove_entry(args.index)
        print("✅ Termin entfernt." if ok else "Kein Termin mit diesem Index.")
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
