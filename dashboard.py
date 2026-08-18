#!/usr/bin/env python3
"""Dashboard-CLI: erzeugt eine lokale HTML-Übersicht und öffnet sie optional.

Zeigt: erzeugte Pakete (mit Freigabe-/Compliance-Status), was gepostet wurde,
und die YouTube-Performance. Reine lokale Datei – kein Server, kein Netz.

    python dashboard.py            # schreibt dashboard.html
    python dashboard.py --open     # + im Browser öffnen (macOS)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from agency.config import ROOT
from agency.dashboard import gather_state, render_html

OUT = ROOT / "dashboard.html"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Erzeugt das lokale Dashboard.")
    parser.add_argument("--open", action="store_true", help="Dashboard im Browser öffnen (macOS).")
    parser.add_argument("--out", default=str(OUT), help="Ausgabepfad der HTML-Datei.")
    args = parser.parse_args(argv)

    state = gather_state()
    Path(args.out).write_text(render_html(state), encoding="utf-8")
    c = state["counts"]
    print(f"✅ Dashboard erzeugt: {args.out}")
    print(f"   {c['pakete']} Pakete · {c['geplant']} bereit · {c['gepostet']} gepostet")
    if args.open:
        try:
            subprocess.run(["open", args.out], check=False)
        except Exception:
            print("   (Konnte nicht automatisch öffnen – Datei manuell im Browser öffnen.)",
                  file=sys.stderr)
    else:
        print(f"   Öffnen mit:  open {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
