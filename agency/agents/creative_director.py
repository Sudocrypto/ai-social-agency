"""Creative Director – finale Qualitäts-/Freigabe-Instanz (läuft auf Opus).

Prüft alle Ergebnisse gegen die Markenstimme, gibt pro Plattform ein Go/No-Go
mit kurzer Begründung und konkreten Nachbesserungen.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class CreativeDirector(BaseAgent):
    key = "creative_director"
    name = "Creative Director"
    max_tokens = 6000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Creative Director der Agentur – die finale Freigabe-Instanz. "
            "Du prüfst kritisch, aber konstruktiv, ob der Content zur Marke passt und "
            "postbar ist.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- Prüfe Markenstimme, Hook-Qualität, Klarheit, Plattform-Fit, CTA.\n"
            "- Gib pro Plattform ein klares ✅ FREIGABE oder ⚠️ NACHBESSERN.\n"
            "- Bei Nachbessern: konkret sagen WAS und WIE. Keine Wischiwaschi-Kritik.\n"
            "- Sei ehrlich – lieber ein ehrliches Nachbessern als ein faules Go."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        pnames = ", ".join(spec(p).name for p in platforms)
        return (
            f"PLATTFORMEN: {pnames}\nTHEMA: {ctx.topic or ctx.pillar}\n\n"
            "FINALE POSTS (Publisher):\n"
            f"{self.prior(ctx, 'publisher', 5000)}\n\n"
            + (
                "COMPLIANCE-PRÜFUNG (unbedingt berücksichtigen – bei RISIKO nachbessern):\n"
                f"{self.prior(ctx, 'compliance_officer', 2500)}\n\n"
                if ctx.get("compliance_officer")
                else ""
            )
            + "STRATEGIE (Kurzfassung):\n"
            f"{self.prior(ctx, 'content_strategist', 1200)}\n\n"
            "AUFGABE: Erstelle die Freigabe-Prüfung als Markdown:\n\n"
            "## Gesamturteil\n<1–2 Sätze>\n\n"
            "## Freigabe pro Plattform\n"
            "### <Plattform>\n"
            "**Status:** ✅ FREIGABE | ⚠️ NACHBESSERN\n"
            "**Begründung:** <kurz>\n"
            "**Nachbesserung (falls nötig):** <konkret>\n\n"
            "## Markenstimme-Check\n<passt/passt nicht + warum>\n\n"
            "Nur das Markdown."
        )
