#!/usr/bin/env python3
"""Preflight-Check vor einem Lauf: prüft Keys, Pakete, ffmpeg, Config, Budget.

    python doctor.py                              # Default-Config (brand_config.yaml)
    python doctor.py --config brand_config.ki.yaml
    python doctor.py --config brand_config.ki.yaml --no-video   # ohne Video-Checks

Exit-Code: 0 = alles ok/nur Warnungen, 1 = harter Fehler (FAIL) gefunden.
"""

from __future__ import annotations

import argparse
import sys

from agency.config import load_config
from agency.doctor import FAIL, OK, WARN, run_checks, worst_status

_ICON = {OK: "✅", WARN: "⚠️ ", FAIL: "❌"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Preflight-Check der Agency-Umgebung.")
    p.add_argument("--config", default=None, help="Pfad zur brand_config.yaml.")
    p.add_argument("--no-video", action="store_true",
                   help="Video-Checks (FAL_KEY/ffmpeg) nur als Info, nicht als Warnung.")
    args = p.parse_args(argv)

    cfg = load_config(args.config) if args.config else load_config()
    checks = run_checks(cfg, needs_video=not args.no_video)

    print("Preflight-Check\n" + "─" * 60)
    for c in checks:
        print(f"{_ICON[c.status]} {c.name}: {c.detail}")
        if c.hint and c.status != OK:
            print(f"     → {c.hint}")
    print("─" * 60)

    overall = worst_status(checks)
    if overall == OK:
        print("Alles bereit. Du kannst den Lauf starten. 🚀")
        return 0
    if overall == WARN:
        print("Startklar mit Einschränkungen (siehe ⚠️ oben) – Text/Content läuft, "
              "Video ggf. nicht.")
        return 0
    print("Es gibt harte Fehler (❌). Bitte oben beheben, bevor du startest.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
