"""Schreibt das Review-Paket nach /output/{datum}/{plattform}/...

Struktur (Etappe A – wächst mit weiteren Agents):
  /output/{datum}/{plattform}/post.md
  /output/{datum}/{plattform}/meta.json
  /output/{datum}/review.md   (konsolidierte Übersicht zur Freigabe)
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import ROOT
from .context import RunContext
from .platforms import resolve_platforms, spec

OUTPUT_ROOT = ROOT / "output"


def _split_by_platform(markdown: str, platform_keys: list[str]) -> dict[str, str]:
    """Zerlegt das Copywriter-Markdown anhand der '## <Plattform>'-Überschriften.

    Ordnet Abschnitte den Plattform-Keys zu, indem der Plattform-Anzeigename
    in der Überschrift gesucht wird. Findet sich nichts, bekommt jede Plattform
    den vollen Text (fail-safe, nie Datenverlust).
    """
    result: dict[str, str] = {}
    lines = markdown.splitlines()
    # Sammle (start_index, platform_key) für jede erkannte Plattform-Überschrift.
    marks: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        heading = line[3:].strip().lower()
        for pk in platform_keys:
            name = spec(pk).name.lower()
            short = name.split(" ")[0]  # "x", "instagram", "facebook", "youtube"
            if name in heading or short in heading:
                marks.append((i, pk))
                break

    if not marks:
        return {pk: markdown.strip() for pk in platform_keys}

    for idx, (start, pk) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        result[pk] = "\n".join(lines[start:end]).strip()

    # Plattformen ohne erkannten Abschnitt: vollen Text als Fallback.
    for pk in platform_keys:
        result.setdefault(pk, markdown.strip())
    return result


def write_package(ctx: RunContext) -> Path:
    """Persistiert alle bisherigen Agent-Ergebnisse als Review-Paket.

    Gibt den Pfad zum Tages-Ordner zurück.
    """
    day_dir = OUTPUT_ROOT / ctx.run_date
    day_dir.mkdir(parents=True, exist_ok=True)

    platform_keys = resolve_platforms(ctx.platform)
    copy_md = str(ctx.get("copywriter", "") or "")
    per_platform = _split_by_platform(copy_md, platform_keys)

    for pk in platform_keys:
        s = spec(pk)
        pdir = day_dir / pk
        pdir.mkdir(parents=True, exist_ok=True)

        (pdir / "post.md").write_text(
            per_platform.get(pk, "").strip() + "\n", encoding="utf-8"
        )

        meta = {
            "plattform": s.name,
            "pillar": ctx.pillar,
            "thema": ctx.topic or ctx.pillar,
            "titel": (ctx.topic or ctx.pillar),
            "description": None,          # wird später vom SEO-Agent gefüllt
            "geplanter_post_zeitpunkt": None,
            "video_kosten_eur": 0.0,      # wird später vom Video-Producer gefüllt
        }
        (pdir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    _write_review(ctx, day_dir, platform_keys)
    return day_dir


def _write_review(ctx: RunContext, day_dir: Path, platform_keys: list[str]) -> None:
    lines: list[str] = []
    lines.append(f"# Review-Paket – {ctx.config.brand_name}")
    lines.append("")
    lines.append(f"**Datum:** {ctx.run_date}  ")
    lines.append(f"**Content-Pillar:** {ctx.pillar}  ")
    lines.append(f"**Thema:** {ctx.topic or '(aus Pillar abgeleitet)'}  ")
    lines.append(f"**Plattformen:** {', '.join(spec(p).name for p in platform_keys)}  ")
    lines.append(f"**Varianten je Plattform:** {ctx.count}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Inhalte pro Plattform")
    lines.append("")
    for pk in platform_keys:
        lines.append(f"- **{spec(pk).name}** → `{pk}/post.md`")
    lines.append("")
    lines.append("## Kosten (LLM, Schätzung)")
    lines.append("")
    lines.append("| Agent | Modell | Input-Tok | Output-Tok | USD |")
    lines.append("|---|---|---:|---:|---:|")
    for e in ctx.cost_log:
        lines.append(
            f"| {e['agent']} | {e['model']} | {e['input_tokens']} | "
            f"{e['output_tokens']} | {e['cost_usd']:.4f} |"
        )
    lines.append(f"| **Summe** | | | | **{ctx.total_cost_usd:.4f}** |")
    lines.append("")
    (day_dir / "review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
