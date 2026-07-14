"""Trend-Scout – recherchiert aktuelle Themen, Formate und Hooks pro Plattform.

Nutzt das Web-Search-Tool des SDK (abschaltbar per --no-websearch). Ohne
Websuche arbeitet er aus Modellwissen.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class TrendScout(BaseAgent):
    key = "trend_scout"
    name = "Trend-Scout"
    max_tokens = 6000
    uses_web_search = True

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Trend-Scout einer Social-Media-Agentur. Du findest heraus, "
            "was JETZT auf den Plattformen funktioniert, damit der Content nicht an "
            "aktuellen Trends vorbeiläuft.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- Wenn dir Web-Suche zur Verfügung steht, recherchiere aktuelle Trends, "
            "Formate, Sounds/Hooks und nenne konkrete, aktuelle Beispiele.\n"
            "- Ohne Web-Suche: klar kennzeichnen, dass es auf Erfahrungswissen basiert.\n"
            "- Fokussiere auf das Thema Auswandern/Perpetual Travel und die Zielgruppe.\n"
            "- Keine erfundenen Statistiken. Lieber ehrlich 'unsicher' als Fake-Zahlen."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        pnames = ", ".join(spec(p).name for p in platforms)
        thema = ctx.topic or f"Content-Pillar: {ctx.pillar}"
        ws = "MIT Live-Websuche" if (self.uses_web_search and ctx.websearch) else "OHNE Websuche (Modellwissen)"
        return (
            f"AUFGABE ({ws}): Recherchiere aktuelle Trends rund um » {thema} «.\n"
            f"Plattformen: {pnames}\n\n"
            "Liefere Markdown mit dieser Struktur:\n\n"
            "## Aktuelle Trends & Formate\n"
            "- <Trend/Format mit kurzer Einordnung, warum relevant>\n\n"
            "## Erfolgreiche Hook-Muster (pro Plattform)\n"
            "### <Plattform>\n- <Hook-Idee/Format>\n\n"
            "## Do & Don't gerade\n- <konkrete Empfehlung>\n\n"
            "## Empfohlene Angles für dieses Thema\n"
            "- <3–5 konkrete Content-Angles, die zur Marke passen>\n\n"
            "Halte es kompakt und umsetzbar. Nur das Markdown."
        )
