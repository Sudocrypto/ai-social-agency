"""Schreibt das komplette Review-Paket nach /output/{datum}/...

Pro Plattform (/output/{datum}/{plattform}/):
  post.md              finaler, postbarer Text (Publisher)
  video_script.md      Skript inkl. Shotlist (Scriptwriter), falls relevant
  post_production.md    Schnittplan (Post-Production), falls relevant
  visual_prompts.md    Bild-/Video-Prompts + Thumbnail (Visual Designer)
  broll/               generierte .mp4 (Render) bzw. Plan + Prompts (Dry-Run)
  meta.json            Titel, Description, Keywords, Hashtags, Video-Kosten

Auf Lauf-Ebene (/output/{datum}/):
  trends.md, strategy.md, community.md, growth.md, director_review.md
  review.md            konsolidierte Übersicht zur Freigabe
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .config import ROOT
from .context import RunContext
from .platforms import resolve_platforms, spec
from .textutils import split_by_platform

OUTPUT_ROOT = ROOT / "output"

_SEO_FIELDS = {
    "titel": re.compile(r"\*\*Titel:\*\*\s*(.+)", re.IGNORECASE),
    "description": re.compile(r"\*\*Description:\*\*\s*(.+)", re.IGNORECASE),
    "keywords": re.compile(r"\*\*Keywords:\*\*\s*(.+)", re.IGNORECASE),
    "hashtags": re.compile(r"\*\*Hashtags:\*\*\s*(.+)", re.IGNORECASE),
}


def _parse_seo(section: str) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for field, rx in _SEO_FIELDS.items():
        m = rx.search(section or "")
        out[field] = m.group(1).strip() if m else None
    return out


def _has_content(text: str) -> bool:
    # Mehr als nur die Plattform-Überschrift?
    stripped = "\n".join(
        ln for ln in (text or "").splitlines() if not ln.startswith("## ")
    ).strip()
    return bool(stripped)


def write_package(ctx: RunContext) -> Path:
    """Persistiert alle Agent-Ergebnisse als Review-Paket. Gibt den Tages-Ordner zurück."""
    day_dir = OUTPUT_ROOT / ctx.run_date
    day_dir.mkdir(parents=True, exist_ok=True)
    platform_keys = resolve_platforms(ctx.platform)

    # Konsolidierte Markdown-Blobs pro Agent, nach Plattform zerlegt.
    posts = split_by_platform(str(ctx.get("publisher", "") or ""), platform_keys)
    if not any(_has_content(v) for v in posts.values()):
        # Fallback: falls Publisher nichts lieferte, lektorierten/Copy-Text nehmen.
        posts = split_by_platform(
            str(ctx.get("editor", "") or ctx.get("copywriter", "") or ""), platform_keys
        )
    scripts = split_by_platform(str(ctx.get("video_scriptwriter", "") or ""), platform_keys)
    prod = split_by_platform(str(ctx.get("post_production", "") or ""), platform_keys)
    visuals = split_by_platform(str(ctx.get("visual_designer", "") or ""), platform_keys)
    seo = split_by_platform(str(ctx.get("seo_hashtag", "") or ""), platform_keys)
    video = ctx.get("video_producer", {}) or {}
    video_pp = video.get("per_platform", {}) if isinstance(video, dict) else {}

    for pk in platform_keys:
        s = spec(pk)
        pdir = day_dir / pk
        pdir.mkdir(parents=True, exist_ok=True)

        (pdir / "post.md").write_text((posts.get(pk, "").strip() + "\n"), encoding="utf-8")

        if _has_content(scripts.get(pk, "")):
            (pdir / "video_script.md").write_text(
                scripts[pk].strip() + "\n", encoding="utf-8"
            )
        if _has_content(prod.get(pk, "")):
            (pdir / "post_production.md").write_text(
                prod[pk].strip() + "\n", encoding="utf-8"
            )
        if _has_content(visuals.get(pk, "")):
            (pdir / "visual_prompts.md").write_text(
                visuals[pk].strip() + "\n", encoding="utf-8"
            )

        _write_broll(pdir, video_pp.get(pk, {}), video)

        seo_fields = _parse_seo(seo.get(pk, ""))
        meta = {
            "plattform": s.name,
            "pillar": ctx.pillar,
            "thema": ctx.topic or ctx.pillar,
            "titel": seo_fields.get("titel") or (ctx.topic or ctx.pillar),
            "description": seo_fields.get("description"),
            "keywords": seo_fields.get("keywords"),
            "hashtags": seo_fields.get("hashtags"),
            "geplanter_post_zeitpunkt": None,
            "video_modus": (video.get("mode") if isinstance(video, dict) else None),
            "video_modell": (video.get("model") if isinstance(video, dict) else None),
            "video_kosten_eur": ctx.video_cost_for(pk),
        }
        (pdir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    _write_runlevel(ctx, day_dir)
    _write_review(ctx, day_dir, platform_keys, video)
    return day_dir


def _write_broll(pdir: Path, pdata: dict, video: dict) -> None:
    clips = pdata.get("clips", []) if isinstance(pdata, dict) else []
    if not clips:
        return
    broll = pdir / "broll"
    broll.mkdir(parents=True, exist_ok=True)

    lines = ["# B-Roll-Plan", ""]
    lines.append(f"Modus: {video.get('mode', 'dry_run')} · Modell: {video.get('model', '?')}")
    lines.append("")
    lines.append("| # | Sek. | geschätzte Kosten (€) | Status | Prompt |")
    lines.append("|---|---:|---:|---|---|")
    for c in clips:
        if c.get("skipped"):
            status = f"übersprungen ({c.get('reason', '')})"
        elif c.get("rendered"):
            status = "gerendert"
        else:
            status = "geplant (Dry-Run)"
        prompt_short = (c["prompt"][:80] + "…") if len(c["prompt"]) > 80 else c["prompt"]
        lines.append(
            f"| {c['index']} | {c['seconds']} | {c['est_cost_eur']:.2f} | {status} | {prompt_short} |"
        )
        num = f"{c['index']:02d}"
        if c.get("rendered") and c.get("data"):
            (broll / f"clip_{num}.mp4").write_bytes(c["data"])
        elif not c.get("skipped"):
            # Dry-Run: Prompt als Textdatei ablegen, damit später leicht renderbar.
            (broll / f"clip_{num}.prompt.txt").write_text(
                c["prompt"] + "\n", encoding="utf-8"
            )
    (broll / "PLAN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_runlevel(ctx: RunContext, day_dir: Path) -> None:
    mapping = {
        "trends.md": ("trend_scout", "Trend-Recherche"),
        "strategy.md": ("content_strategist", "Strategie / Redaktionsplan"),
        "community.md": ("community_manager", "Community-Material"),
        "growth.md": ("growth_analyst", "Growth-Plan"),
        "director_review.md": ("creative_director", "Creative-Director-Freigabe"),
    }
    for filename, (key, title) in mapping.items():
        content = str(ctx.get(key, "") or "").strip()
        if content:
            (day_dir / filename).write_text(f"# {title}\n\n{content}\n", encoding="utf-8")


def _write_review(ctx: RunContext, day_dir: Path, platform_keys: list[str], video: dict) -> None:
    L: list[str] = []
    L.append(f"# Review-Paket – {ctx.config.brand_name}")
    L.append("")
    L.append(f"**Datum:** {ctx.run_date}  ")
    L.append(f"**Content-Pillar:** {ctx.pillar}  ")
    L.append(f"**Thema:** {ctx.topic or '(aus Pillar abgeleitet)'}  ")
    L.append(f"**Plattformen:** {', '.join(spec(p).name for p in platform_keys)}  ")
    L.append(f"**Varianten je Plattform:** {ctx.count}  ")
    L.append(f"**Video-Modus:** {video.get('mode', '—') if isinstance(video, dict) else '—'}")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Dateien pro Plattform")
    L.append("")
    for pk in platform_keys:
        pdir = day_dir / pk
        files = sorted(
            str(p.relative_to(day_dir)) for p in pdir.rglob("*") if p.is_file()
        )
        L.append(f"**{spec(pk).name}**")
        for f in files:
            L.append(f"- `{f}`")
        L.append("")
    L.append("## Lauf-Dokumente")
    for f in ("trends.md", "strategy.md", "community.md", "growth.md", "director_review.md"):
        if (day_dir / f).exists():
            L.append(f"- `{f}`")
    L.append("")
    L.append("## Freigabe (Creative Director)")
    L.append("")
    director = str(ctx.get("creative_director", "") or "").strip()
    L.append(director if director else "_(kein Director-Urteil vorhanden)_")
    L.append("")
    L.append("## Kosten")
    L.append("")
    L.append("### LLM (Schätzung, USD)")
    L.append("| Agent | Modell | Input-Tok | Output-Tok | USD |")
    L.append("|---|---|---:|---:|---:|")
    for e in ctx.cost_log:
        L.append(
            f"| {e['agent']} | {e['model']} | {e['input_tokens']} | "
            f"{e['output_tokens']} | {e['cost_usd']:.4f} |"
        )
    L.append(f"| **Summe** | | | | **{ctx.total_cost_usd:.4f}** |")
    L.append("")
    if ctx.video_log:
        L.append("### Video (Schätzung, EUR)")
        L.append("| Plattform | Clip | Sek. | Modell | € | gerendert |")
        L.append("|---|---:|---:|---|---:|---|")
        for e in ctx.video_log:
            L.append(
                f"| {e['plattform']} | {e['clip']} | {e['sekunden']} | {e['modell']} | "
                f"{e['kosten_eur']:.2f} | {'ja' if e['gerendert'] else 'nein (Dry-Run)'} |"
            )
        L.append(f"| **Summe** | | | | **{ctx.total_video_cost_eur:.2f}** | |")
        L.append("")
    (day_dir / "review.md").write_text("\n".join(L) + "\n", encoding="utf-8")
