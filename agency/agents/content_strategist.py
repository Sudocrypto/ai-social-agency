"""Content-Stratege – Redaktionsplan, Themenwahl pro Pillar, Kampagnen-Idee."""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class ContentStrategist(BaseAgent):
    key = "content_strategist"
    name = "Content-Stratege"
    max_tokens = 6000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Content-Stratege der Agentur. Aus Ziel + Trend-Recherche "
            "machst du einen klaren, umsetzbaren Plan für diesen Durchlauf.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- Denke in Content-Pillars und in einem konkreten roten Faden.\n"
            "- Priorisiere: was ist der EINE stärkste Angle für diesen Durchlauf?\n"
            "- Berücksichtige plattformspezifische Stärken.\n"
            "- Konkrete Vorgaben, an denen sich die anderen Agents entlanghangeln können."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        pnames = ", ".join(spec(p).name for p in platforms)
        thema = ctx.topic or f"aus Pillar abgeleitet: {ctx.pillar}"
        return (
            f"THEMA: {thema}\nPILLAR: {ctx.pillar}\nPLATTFORMEN: {pnames}\n"
            f"Varianten je Plattform: {ctx.count}\n\n"
            "TREND-RECHERCHE (vom Trend-Scout):\n"
            f"{self.prior(ctx, 'trend_scout')}\n\n"
            "AUFGABE: Erstelle den Redaktions-/Strategieplan als Markdown:\n\n"
            "## Kern-Angle\n<der eine stärkste Angle in 1–2 Sätzen>\n\n"
            "## Kernbotschaft & Takeaway\n<was soll hängenbleiben>\n\n"
            "## Plan pro Plattform\n"
            "### <Plattform>\n- Format: <…>\n- Angle: <…>\n- Ziel/CTA: <…>\n\n"
            "## Kampagnen-Idee (optional, für Folgerunden)\n- <Idee>\n\n"
            "Nur das Markdown."
        )
