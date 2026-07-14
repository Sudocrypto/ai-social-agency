"""Video-Scriptwriter – Skripte für YouTube (Langform) + Reels/Shorts.

Inkl. Shotlist und Hook in den ersten 3 Sekunden.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class VideoScriptwriter(BaseAgent):
    key = "video_scriptwriter"
    name = "Video-Scriptwriter"
    max_tokens = 8000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Video-Scriptwriter der Agentur. Du schreibst Skripte, die "
            "in Ich-Perspektive gesprochen werden und in den ersten 3 Sekunden fesseln.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- YouTube = Langform (Intro-Hook, Kapitel, Payoff, CTA).\n"
            "- Reels/Shorts/X = kurz, schnell, ein Gedanke, harter Hook in Sek. 0–3.\n"
            "- Immer eine Shotlist: was ist im Bild (ich selbst vs. B-Roll).\n"
            "- Sprich, wie ich rede – kein Teleprompter-Stelzen-Deutsch."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        thema = ctx.topic or f"Pillar: {ctx.pillar}"
        blocks = []
        for p in platforms:
            s = spec(p)
            longform = "Langform" if p == "youtube" else "Kurzform (Reel/Short)"
            blocks.append(f"### {s.name} ({longform})")
        briefs = "\n".join(blocks)
        return (
            f"THEMA: {thema}\nPILLAR: {ctx.pillar}\n\n"
            "STRATEGIE:\n"
            f"{self.prior(ctx, 'content_strategist')}\n\n"
            "AUFGABE: Schreibe Video-Skripte pro Plattform als Markdown:\n\n"
            f"{briefs}\n\n"
            "Struktur pro Plattform:\n"
            "## <Plattform>\n"
            "**Hook (0–3 Sek.):** <Text>\n\n"
            "**Skript:**\n<gesprochener Text, ggf. mit [Kapitel]-Markern>\n\n"
            "**Shotlist:**\n"
            "| Zeit/Szene | Bild (ich / B-Roll) | Hinweis |\n"
            "|---|---|---|\n"
            "| … | … | … |\n\n"
            "**CTA (gesprochen):** <Text>\n\n"
            "Nur das Markdown."
        )
