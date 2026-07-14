"""Video-Producer – erzeugt KI-B-Roll-Clips aus den Prompts des Visual Designers.

Kein LLM-Agent, sondern ein Tool-Schritt. Standard = Dry-Run: parst die
VIDEO-PROMPT-Zeilen, plant Clips, schätzt Kosten und schreibt einen Plan – ruft
aber KEINE fal.ai-API. Erst mit --render-video werden echte .mp4 gerendert.
In beiden Fällen gilt der Kosten-Cap (max_video_budget_eur) pro Durchlauf.
"""

from __future__ import annotations

import re

from ..context import RunContext
from ..platforms import resolve_platforms, spec
from ..textutils import split_by_platform
from ..video import fal_client

# Zeilen wie: "VIDEO-PROMPT [8s]: a cinematic drone shot over Bangkok at dusk"
_PROMPT_RE = re.compile(r"VIDEO-PROMPT\s*\[(\d+)\s*s\]:\s*(.+)", re.IGNORECASE)


class VideoProducer:
    """Tool-Schritt (implementiert dieselbe Schnittstelle wie ein Agent)."""

    key = "video_producer"
    name = "Video-Producer"

    def __init__(self, llm=None) -> None:  # llm nicht genutzt, für einheitliche Signatur
        pass

    def run(self, ctx: RunContext) -> dict:
        cfg = ctx.config
        model = cfg.video.get("video_modell", "veo-3.1")
        max_s = int(cfg.video.get("max_clip_sekunden", 8))
        budget = float(cfg.video.get("max_video_budget_eur", 5.0))
        render = ctx.render_video and bool(cfg.fal_key)

        platforms = resolve_platforms(ctx.platform)
        per_platform_md = split_by_platform(
            str(ctx.get("visual_designer", "") or ""), platforms
        )

        result: dict[str, dict] = {}
        spent = 0.0  # kumulierte (geschätzte) Kosten fürs Cap

        for pk in platforms:
            clips: list[dict] = []
            for idx, (secs, prompt) in enumerate(self._prompts(per_platform_md[pk], max_s), 1):
                est = fal_client.estimate_cost_eur(model, secs)

                if spent + est > budget:
                    clips.append(
                        {
                            "index": idx, "prompt": prompt, "seconds": secs,
                            "model": model, "est_cost_eur": est,
                            "rendered": False, "skipped": True,
                            "reason": f"Kosten-Cap {budget:.2f} EUR erreicht",
                            "data": None,
                        }
                    )
                    continue

                data = None
                rendered = False
                if render:
                    try:
                        data = fal_client.render_clip(
                            prompt=prompt, seconds=secs, model=model, api_key=cfg.fal_key
                        )
                        rendered = True
                    except Exception as exc:  # Render darf den Lauf nie killen
                        clips.append(
                            {
                                "index": idx, "prompt": prompt, "seconds": secs,
                                "model": model, "est_cost_eur": est,
                                "rendered": False, "skipped": True,
                                "reason": f"Render-Fehler: {exc}", "data": None,
                            }
                        )
                        continue

                spent += est
                ctx.record_video(
                    plattform=pk, clip=idx, sekunden=secs, modell=model,
                    kosten_eur=est, gerendert=rendered,
                )
                clips.append(
                    {
                        "index": idx, "prompt": prompt, "seconds": secs,
                        "model": model, "est_cost_eur": est,
                        "rendered": rendered, "skipped": False, "data": data,
                    }
                )
            result[pk] = {"clips": clips}

        out = {
            "mode": "render" if render else "dry_run",
            "model": model,
            "budget_eur": budget,
            "per_platform": result,
        }
        ctx.set(self.key, out)
        return out

    @staticmethod
    def _prompts(markdown: str, max_s: int):
        """Extrahiert (sekunden, prompt) aus VIDEO-PROMPT-Zeilen, gekappt auf max_s."""
        for m in _PROMPT_RE.finditer(markdown or ""):
            secs = min(int(m.group(1)), max_s)
            prompt = m.group(2).strip()
            if prompt:
                yield secs, prompt
