#!/usr/bin/env python3
"""Voll-Automatik: Content → Freigabe/Compliance → KI-Video → Schnitt → Upload → Tracking.

Ein Befehl, der die ganze Kette verkettet. Macht so viel automatisch wie möglich
und stoppt sauber, sobald etwas fehlt (FAL_KEY, ffmpeg, YouTube-OAuth) oder ein
Sicherheits-Gate greift.

⚠️ Sicherheit & Kosten: Alles, was der Creative Director (NACHBESSERN) oder der
Compliance-Prüfer (RISIKO) markiert, wird NICHT hochgeladen. Video kostet echtes
fal.ai-Guthaben und wird deshalb NUR mit --video und NUR NACH bestandenem Gate
gerendert – ein blockierter Lauf gibt nie Video-Geld aus. Der Upload passiert nur
mit --post. Für Finanz-/Krypto-Content: erst voll scharf schalten, wenn ein Anwalt
den Disclaimer/das Konzept geprüft hat.

    python auto.py --config brand_config.ki.yaml --pillar tools --topic "…"           # nur Text
    python auto.py --config brand_config.ki.yaml --pillar tools --topic "…" --video   # + KI-Video
    python auto.py --config brand_config.ki.yaml --pillar tools --topic "…" --video --post  # + Upload
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agency.app import build_pipeline
from agency.assembly.builder import ffmpeg_available, render
from agency.assembly.scaffold import auto_plan
from agency.config import load_config
from agency.context import RunContext
from agency.llm import LLM
from agency.output_writer import write_package
from agency.platforms import ALL_PLATFORMS
from agency.publishing.approval import gate_status
from agency.publishing.credentials import load_credentials
from agency.publishing.loader import load_post
from agency.publishing.post_log import record_post
from agency.publishing.registry import get_publisher


def _log(msg: str) -> None:
    print(msg, flush=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Voll-Automatik von Content bis Upload.")
    p.add_argument("--pillar", required=True)
    p.add_argument("--platform", default="youtube", choices=ALL_PLATFORMS)
    p.add_argument("--topic", default=None)
    p.add_argument("--config", default=None)
    p.add_argument("--music", default=None, help="Optionale Hintergrundmusik-Datei.")
    p.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--no-websearch", action="store_true")
    p.add_argument("--max-budget", type=float, default=None,
                   help="Video-Budget-Cap in EUR NUR für diesen Lauf (überschreibt Config).")
    p.add_argument("--max-clip-seconds", type=int, default=None,
                   help="Max. Clip-Länge in Sekunden NUR für diesen Lauf (überschreibt Config).")
    p.add_argument("--video", action="store_true",
                   help="KI-Video rendern (kostet fal.ai-Guthaben). Ohne dies nur Text/Prompts.")
    p.add_argument("--post", action="store_true",
                   help="Am Ende WIRKLICH hochladen (sonst nur bis zum fertigen Video).")
    p.add_argument("--force", action="store_true",
                   help="Freigabe-/Compliance-Sperre überstimmen (nicht empfohlen).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config(args.config) if args.config else load_config()
    if not cfg.anthropic_api_key:
        _log("FEHLER: ANTHROPIC_API_KEY fehlt (.env).")
        return 2
    # Kosten-Overrides nur für diesen Lauf (Config bleibt unverändert).
    if args.max_budget is not None:
        cfg.video["max_video_budget_eur"] = args.max_budget
    if args.max_clip_seconds is not None:
        cfg.video["max_clip_sekunden"] = args.max_clip_seconds
    pk = args.platform

    # 1) Content generieren – IMMER ohne echtes Video-Rendern (kostet kein fal.ai-Geld).
    # Das Video entsteht erst nach dem Gate (Schritt 3), nur mit --video.
    _log(f"[1/5] Content generieren … (Plattform: {pk})")
    ctx = RunContext(
        config=cfg, pillar=args.pillar, platform=pk, count=1,
        topic=args.topic, websearch=cfg.websearch_default and not args.no_websearch,
        render_video=False, effort_override=args.effort,
    )
    llm = LLM(cfg.anthropic_api_key)
    build_pipeline(llm).run(ctx)
    day_dir = write_package(ctx)
    _log(f"      Paket: {day_dir}  ·  LLM ~${ctx.total_cost_usd:.4f}")
    if ctx.total_video_cost_eur > 0:
        _log(f"      (Video-Schätzung ~{ctx.total_video_cost_eur:.2f}€ – noch NICHTS gerendert, "
             "kein Geld ausgegeben. Mit --video wird nach der Freigabe gerendert.)")

    # Abbruch, wenn die Content-Generierung faktisch fehlgeschlagen ist (z. B. leeres
    # Anthropic-Guthaben): kein Publisher-/Director-Ergebnis -> nichts zum Freigeben.
    if not ctx.get("publisher") or not ctx.get("creative_director"):
        _log("      ❌ Content-Generierung fehlgeschlagen – kein vollständiges Paket.")
        if ctx.credit_error:
            _log("      Grund: Anthropic-Guthaben zu niedrig. Aufladen unter "
                 "console.anthropic.com → Plans & Billing, dann erneut starten.")
        elif ctx.errors:
            _log(f"      Erster Fehler ({ctx.errors[0]['agent']}): {ctx.errors[0]['message']}")
        return 2

    # 2) Sicherheits-Gate (Director + Compliance) ------------------------------
    gate = gate_status(day_dir, pk)
    _log(f"[2/5] Freigabe-Gate: {gate['reason']}")
    if not gate["allowed"] and not args.force:
        _log("      ⛔ Blockiert – kein Upload. (Mit --force überstimmbar, nicht empfohlen.)")
        _log(f"      Prüfe {day_dir/'director_review.md'} und {day_dir/'compliance_report.md'}.")
        return 1
    if gate["allowed"]:
        note = " (Tipps im director_review.md)" if gate.get("tier") == "hinweise" else ""
        _log(f"      ✅ Freigabe erteilt – Upload läuft.{note}")

    # 3) KI-Video: NUR mit --video und NUR jetzt (nach bestandenem Gate) -------
    # Erst ab hier entstehen fal.ai-Kosten – ein blockierter Lauf zahlt nie Video.
    if not args.video:
        _log("[3/5] ⏹  Kein Video gerendert (kein --video → kein fal.ai-Geld ausgegeben). "
             "Text, Skript und Video-Prompts sind fertig im Paket.")
        _log("      Für echtes KI-Video den Lauf mit --video wiederholen.")
        return 0
    if not cfg.fal_key:
        _log("[3/5] ⏹  --video gesetzt, aber kein FAL_KEY in .env → kann nicht rendern.")
        return 0
    if not ffmpeg_available():
        _log("[3/5] ⏹  --video gesetzt, aber ffmpeg fehlt → kann nicht schneiden.")
        return 0

    # Jetzt – nach der Freigabe – echte Clips rendern.
    from agency.agents.video_producer import VideoProducer

    ctx.render_video = True
    ctx.video_log.clear()  # etwaige Dry-Run-Schätzung verwerfen
    _log("[3/5] KI-Clips rendern … (kostet jetzt fal.ai-Guthaben)")
    VideoProducer().run(ctx)
    write_package(ctx)  # gerenderte .mp4 in broll/ persistieren
    _log(f"      Clips gerendert · Video ~{ctx.total_video_cost_eur:.2f}€")

    plan = auto_plan(day_dir, pk, music=args.music)
    if plan is None:
        _log("      ⏹  Keine gerenderten Clips – evtl. keine VIDEO-PROMPTs oder Budget zu klein.")
        return 0
    final = day_dir / pk / plan.output
    _log(f"      Video schneiden … ({len(plan.segments)} Segmente, ~{plan.total_duration}s)")
    res = render(plan, final, dry_run=False)
    if not res["ok"]:
        _log(f"      ❌ Render-Fehler: {res.get('error')}")
        return 1
    _log(f"      ✅ Video fertig: {final}")

    # 4) Upload (nur mit --post) ----------------------------------------------
    if not args.post:
        _log("[4/5] ⏸  Video fertig, aber NICHT hochgeladen (kein --post). "
             f"Manuell prüfen: {final}")
        _log("      Mit --post lädt die Automatik direkt hoch.")
        return 0
    _log("[4/5] Upload zu YouTube …")
    post = load_post(day_dir, pk)
    post.media = [Path(final)]
    creds = load_credentials()
    result = get_publisher(pk).publish(post, creds, dry_run=False)
    if not result.ok:
        _log(f"      ❌ Upload fehlgeschlagen: {result.error}")
        return 1
    _log(f"      ✅ Hochgeladen: {result.url or '(kein Link)'}")
    for w in result.warnings:
        _log(f"      ⚠️  {w}")

    # 5) Tracking fürs Dashboard ----------------------------------------------
    record_post(pk, result.url, day_dir.name)
    if result.url:
        try:
            from agency.monitoring.tracker import Tracker
            Tracker().add(result.url, thema=args.topic or args.pillar)
        except Exception:
            pass
    _log("[5/5] ✅ Fertig – ins Post-Log/Tracking übernommen. Dashboard: python dashboard.py --open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
