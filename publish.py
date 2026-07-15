#!/usr/bin/env python3
"""Phase-2-CLI: freigegebenen Content aus einem Review-Paket posten.

Standard ist DRY-RUN (nur Validierung + Vorschau, kein Netz). Echtes Posten
braucht --live und eine Bestätigung pro Plattform (JA), weil es nach außen
wirksam und nicht umkehrbar ist.

Beispiele:
    python publish.py                              # neuestes Paket, Dry-Run, alle Plattformen
    python publish.py --date 2026-07-14 --platform x
    python publish.py --platform facebook --live   # echt posten (mit Rückfrage)
    python publish.py --platform instagram --ig-media-url https://.../reel.mp4 --live
    python publish.py --platform youtube --yt-video /pfad/final.mp4 --live
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agency.config import ROOT
from agency.platforms import ALL_PLATFORMS
from agency.publishing import get_publisher
from agency.publishing.approval import load_approvals, load_compliance
from agency.publishing.credentials import load_credentials
from agency.publishing.loader import load_post

OUTPUT_ROOT = ROOT / "output"


def _latest_day() -> Path | None:
    if not OUTPUT_ROOT.exists():
        return None
    days = sorted((p for p in OUTPUT_ROOT.iterdir() if p.is_dir()), reverse=True)
    return days[0] if days else None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Postet freigegebenen Content pro Plattform.")
    p.add_argument("--date", default=None, help="Paket-Datum (YYYY-MM-DD). Default: neuestes.")
    p.add_argument("--platform", default="all", choices=[*ALL_PLATFORMS, "all"])
    p.add_argument("--variant", type=int, default=1, help="Welche Post-Variante (Default 1).")
    p.add_argument("--live", action="store_true",
                   help="ECHT posten statt Dry-Run (nach außen wirksam, irreversibel).")
    p.add_argument("--yes", action="store_true",
                   help="Bestätigungs-Rückfrage im Live-Modus überspringen (Vorsicht).")
    p.add_argument("--force", action="store_true",
                   help="Auch Plattformen posten, die der Creative Director als "
                        "'⚠️ NACHBESSERN' markiert hat.")
    p.add_argument("--ig-media-url", default=None,
                   help="Öffentlich gehostete Medien-URL für Instagram.")
    p.add_argument("--yt-video", default=None, help="Pfad zur fertigen YouTube-Videodatei.")
    return p


def _confirm(platform_name: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        print(f"   ⏭️  {platform_name}: keine Bestätigung möglich (kein TTY) – übersprungen. "
              "Nutze --yes für unbeaufsichtigtes Posten.", file=sys.stderr)
        return False
    ans = input(f"   ⚠️  Auf {platform_name} WIRKLICH live posten? Tippe JA: ").strip()
    return ans == "JA"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    day_dir = (OUTPUT_ROOT / args.date) if args.date else _latest_day()
    if not day_dir or not day_dir.exists():
        print("FEHLER: Kein Review-Paket gefunden. Erst 'python run.py …' ausführen.",
              file=sys.stderr)
        return 2

    platforms = ALL_PLATFORMS if args.platform == "all" else [args.platform]
    creds = load_credentials()
    approvals = load_approvals(day_dir)
    compliance = load_compliance(day_dir)
    mode = "LIVE" if args.live else "DRY-RUN"
    print(f"Paket: {day_dir.name} · Modus: {mode} · Plattformen: {', '.join(platforms)}\n")

    any_error = False
    for pk in platforms:
        pub = get_publisher(pk)

        # Compliance-Risiko durchsetzen (rechtliche Absicherung).
        comp = compliance.get(pk, {})
        if comp.get("ok") is False and not args.force:
            print(f"• {pub.name}: ⛔ Compliance-Risiko (Prüfer) "
                  "– übersprungen (mit --force überstimmbar).")
            continue

        # Freigabe des Creative Directors durchsetzen.
        approval = approvals.get(pk, {})
        if approval.get("approved") is False and not args.force:
            print(f"• {pub.name}: ⛔ vom Creative Director als NACHBESSERN markiert "
                  "– übersprungen (mit --force überstimmbar).")
            continue
        if approval.get("approved") is None:
            print(f"• {pub.name}: ℹ️  kein Director-Urteil vorhanden.")

        post = load_post(day_dir, pk, variant=args.variant)
        if pk == "instagram" and args.ig_media_url:
            post.media_urls = [args.ig_media_url]
        if pk == "youtube" and args.yt_video:
            post.media = [Path(args.yt_video)]

        do_live = args.live
        if do_live:
            # Vor jedem echten Post: validieren + bestätigen.
            errs = pub.validate(post)
            if errs:
                print(f"• {pub.name}: ❌ Validierung fehlgeschlagen: {'; '.join(errs)}")
                any_error = True
                continue
            if not _confirm(pub.name, args.yes):
                print(f"• {pub.name}: übersprungen (nicht bestätigt).")
                continue

        result = pub.publish(post, creds, dry_run=not do_live)
        icon = "✅" if result.ok else "❌"
        print(f"• {pub.name}: {icon} {result.action}")
        if result.url:
            print(f"    → {result.url}")
        for w in result.warnings:
            print(f"    ⚠️  {w}")
        if result.error:
            print(f"    Fehler: {result.error}")
            any_error = True

    if not args.live:
        print("\nℹ️  Dry-Run – es wurde nichts gepostet. Mit --live echt posten.")
    return 1 if any_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
