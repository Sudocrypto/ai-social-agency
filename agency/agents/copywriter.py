"""Copywriter – schreibt Captions, Hooks, X-Threads und Post-Texte pro Plattform.

Erster vollständiger Agent (Etappe A): erzeugt fertige Post-Texte je Plattform,
inkl. Hook, Caption/Body, CTA und Hashtag-Set – exakt auf die Plattform-Specs
zugeschnitten.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class Copywriter(BaseAgent):
    key = "copywriter"
    name = "Copywriter"
    max_tokens = 8000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Copywriter einer Social-Media-Agentur und schreibst "
            "konsequent in der Stimme der Marke (siehe SPRACHE/STIL – z.B. "
            "Ich-Perspektive bei persönlichen Marken oder eine neutrale News-Stimme "
            "bei anonymen Marken).\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Deine Regeln:\n"
            "- Schreibe wie ein echter Mensch, nicht wie Marketing. Kein Corporate-Sprech.\n"
            "- Der Hook in den ersten Sekunden/Zeilen muss sitzen (Neugier, Konflikt, "
            "konkrete Zahl oder ehrliches Gefühl).\n"
            "- Immer ein klarer, unaufdringlicher CTA am Ende.\n"
            "- Halte dich an die Zeichen- und Hashtag-Vorgaben der jeweiligen Plattform.\n"
            "- Kein Clickbait, keine leeren Versprechen – authentisch und konkret."
        )

    def _platform_brief(self, platform_key: str) -> str:
        s = spec(platform_key)
        return (
            f"### {s.name}\n"
            f"- Ziel-Länge Haupttext: ~{s.max_chars} Zeichen\n"
            f"- Hashtags: {s.hashtag_count}\n"
            f"- Format: {s.format_hint}\n"
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        thema = ctx.topic or f"passend zum Content-Pillar: {ctx.pillar}"
        briefs = "\n".join(self._platform_brief(p) for p in platforms)

        return (
            f"AUFGABE: Schreibe fertige, direkt postbare Texte zum Thema:\n"
            f"» {thema} «\n"
            f"Content-Pillar: {ctx.pillar}\n\n"
            "STRATEGIE (vom Content-Strategen, daran orientieren):\n"
            f"{self.prior(ctx, 'content_strategist')}\n\n"
            f"Erzeuge pro Plattform {ctx.count} eigenständige Post-Variante(n).\n\n"
            f"PLATTFORMEN & VORGABEN:\n{briefs}\n"
            "AUSGABEFORMAT (reines Markdown, exakt diese Struktur):\n\n"
            "## <Plattform-Name>\n"
            "### Post 1\n"
            "**Hook:** <ein Satz>\n\n"
            "**Text:**\n<fertiger Post-Text bzw. bei X ggf. nummerierter Thread>\n\n"
            "**CTA:** <Call-to-Action>\n\n"
            "**Hashtags:** <Hashtags gemäß Vorgabe>\n\n"
            "(bei mehreren Varianten: ### Post 2, ### Post 3, ...)\n\n"
            "Gib NUR das Markdown aus – keine Vorrede, keine Erklärungen."
        )
