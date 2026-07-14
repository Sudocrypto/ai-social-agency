"""Growth-Analyst – definiert KPIs und schlägt Optimierungen für die nächste Runde vor.

Wertet – falls vorhanden – gelieferte Performance-Daten aus. Ohne Daten definiert
er die zu trackenden KPIs und Hypothesen für den nächsten Durchlauf.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class GrowthAnalyst(BaseAgent):
    key = "growth_analyst"
    name = "Growth-Analyst"
    max_tokens = 5000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Growth-Analyst der Agentur. Du machst Erfolg messbar und "
            "leitest konkrete Optimierungen ab.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- Definiere KPIs pro Plattform (z.B. Watchtime, Saves, Shares, Kommentare).\n"
            "- Formuliere testbare Hypothesen für die nächste Runde.\n"
            "- Wenn keine echten Daten vorliegen: klar als Baseline/Annahme kennzeichnen, "
            "keine erfundenen Zahlen."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        pnames = ", ".join(spec(p).name for p in platforms)
        return (
            f"PLATTFORMEN: {pnames}\nTHEMA: {ctx.topic or ctx.pillar}\n\n"
            "AUFGABE: Liefere den Growth-Plan als Markdown:\n\n"
            "## KPIs pro Plattform\n"
            "### <Plattform>\n- <KPI + warum>\n\n"
            "## Hypothesen für die nächste Runde\n- <testbare Hypothese>\n\n"
            "## Was beim nächsten Durchlauf messen/mitgeben\n- <konkret>\n\n"
            "Nur das Markdown."
        )
