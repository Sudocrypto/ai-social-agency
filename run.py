#!/usr/bin/env python3
"""CLI-Entrypoint der AI Social Media Agency.

Beispiel:
    python run.py --pillar auswandern --platform all --count 5
    python run.py --pillar reise --platform instagram --topic "Erster Monat Thailand"
"""

from __future__ import annotations

import argparse
import sys

from agency.agents import Copywriter
from agency.config import load_config
from agency.context import RunContext
from agency.llm import LLM
from agency.pipeline import Pipeline
from agency.output_writer import write_package
from agency.platforms import ALL_PLATFORMS


def _resolve_pillar(value: str, pillars: list[str]) -> str:
    """Erlaubt Kurzformen: '--pillar auswandern' matcht den vollen Pillar-Text."""
    low = value.lower()
    for p in pillars:
        if low in p.lower():
            return p
    return value  # freies Thema als Pillar durchreichen


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Social Media Agency – generiert Content-Review-Pakete."
    )
    parser.add_argument(
        "--pillar", required=True,
        help="Content-Pillar (Kurzform wie 'auswandern' genügt) oder freies Thema.",
    )
    parser.add_argument(
        "--platform", default="all",
        choices=[*ALL_PLATFORMS, "all"],
        help="Zielplattform oder 'all' (Standard).",
    )
    parser.add_argument(
        "--count", type=int, default=1,
        help="Anzahl Post-Varianten pro Plattform (Standard: 1).",
    )
    parser.add_argument(
        "--topic", default=None,
        help="Optionales konkretes Thema (überschreibt die Pillar-Ableitung).",
    )
    parser.add_argument(
        "--no-websearch", action="store_true",
        help="Live-Websuche (Trend-Scout) für kostenlose Testläufe abschalten.",
    )
    parser.add_argument(
        "--config", default=None,
        help="Alternativer Pfad zur brand_config.yaml.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    cfg = load_config(args.config) if args.config else load_config()
    if not cfg.anthropic_api_key:
        print(
            "FEHLER: ANTHROPIC_API_KEY fehlt. Lege eine .env an (Vorlage: .env.example).",
            file=sys.stderr,
        )
        return 2

    pillar = _resolve_pillar(args.pillar, cfg.content_pillars)
    websearch = cfg.websearch_default and not args.no_websearch

    ctx = RunContext(
        config=cfg,
        pillar=pillar,
        platform=args.platform,
        count=max(1, args.count),
        topic=args.topic,
        websearch=websearch,
    )

    llm = LLM(cfg.anthropic_api_key)

    # Etappe A: nur der Copywriter end-to-end. Weitere Agents kommen dazu.
    pipeline = Pipeline(llm, [Copywriter(llm)])
    pipeline.run(ctx)

    day_dir = write_package(ctx)
    print(f"\n✅ Review-Paket erzeugt: {day_dir}")
    print(f"   Übersicht: {day_dir / 'review.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
