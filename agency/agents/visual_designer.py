"""Visual Designer – direkt nutzbare Bild-/Video-Generierungs-Prompts.

Liefert pro Plattform: Bild-Prompts, Video-Prompts (klar markiert für den
Video-Producer), Thumbnail-Idee und ein kurzes Storyboard.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class VisualDesigner(BaseAgent):
    key = "visual_designer"
    name = "Visual Designer"
    max_tokens = 8000

    def system_prompt(self, ctx: RunContext) -> str:
        modus = ctx.config.video.get("video_modus", "broll_only")
        modus_hinweis = (
            "MODUS broll_only: Die generierten Clips sind ILLUSTRATIVE B-Roll-Szenen "
            "(Orte, Atmosphäre, Details) – der Creator bleibt selbst im Bild. Keine "
            "synthetischen Menschen, die ihn ersetzen."
            if modus == "broll_only"
            else "MODUS full_synthetic: Vollständig KI-generierte Szenen erlaubt."
        )
        return (
            "Du bist der Visual Designer der Agentur. Du schreibst konkrete, direkt in "
            "eine KI-Bild-/Video-API einsetzbare Prompts – detailliert zu Motiv, Licht, "
            "Kameraperspektive, Stimmung, Stil.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            f"{modus_hinweis}\n\n"
            "Regeln:\n"
            "- Video-Prompts IMMER exakt so markieren: 'VIDEO-PROMPT [Ns]: <prompt>' "
            "(N = Sekunden, ganze Zahl). Diese Zeilen liest der Video-Producer maschinell.\n"
            "- Bild-Prompts markieren mit 'BILD-PROMPT: <prompt>'.\n"
            "- Prompts auf Englisch (bessere Modell-Ergebnisse), Rest auf Deutsch.\n"
            "- Realistisch, keine überladenen Wunsch-Szenen."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        pnames = ", ".join(spec(p).name for p in platforms)
        max_s = int(ctx.config.video.get("max_clip_sekunden", 8))
        return (
            f"PLATTFORMEN: {pnames}\nMAX. CLIP-LÄNGE: {max_s} Sekunden\n\n"
            "STRATEGIE / SKRIPTE / SCHNITTPLAN (Kontext):\n"
            f"{self.prior(ctx, 'content_strategist', 1500)}\n\n"
            f"{self.prior(ctx, 'post_production', 2000)}\n\n"
            "AUFGABE: Erzeuge pro Plattform die Visual-Prompts als Markdown:\n\n"
            "## <Plattform>\n"
            "**Storyboard:**\n1. <Szene> 2. <Szene> …\n\n"
            "**Video-Prompts (B-Roll):**\n"
            f"- VIDEO-PROMPT [{max_s}s]: <english prompt, illustrative b-roll>\n"
            f"- VIDEO-PROMPT [{max_s}s]: <english prompt>\n\n"
            "**Bild-Prompts:**\n"
            "- BILD-PROMPT: <english prompt>\n\n"
            "**Thumbnail-Idee:**\n<Beschreibung + BILD-PROMPT: <english prompt>>\n\n"
            f"Achte darauf, dass jede Clip-Länge <= {max_s}s ist. Nur das Markdown."
        )
