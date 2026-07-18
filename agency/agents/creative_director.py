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
            "- Vergib pro Plattform GENAU EINE von DREI Stufen:\n"
            "  ✅ FREIGABE – postbar, keine Einwände.\n"
            "  🟡 FREIGABE MIT HINWEISEN – rechtlich/faktisch sauber und postbar, aber du "
            "hast Verbesserungstipps. Diese Stufe BLOCKIERT NICHT; die Tipps sind fürs "
            "nächste Mal. Nutze sie für reine Politur (Hook schärfer, Wort umformulieren, "
            "Kürzung) – NICHT für echte Fehler.\n"
            "  ⚠️ NACHBESSERN – NUR bei echten Blockern, die den Upload verhindern MÜSSEN: "
            "rechtlich riskant, faktisch falsch/irreführend (z. B. unbelegte absolute "
            "Behauptung), fehlende Pflicht-Kennzeichnung, off-brand, gefährlich oder "
            "Plattform-Verstoß. Wähle diese Stufe sparsam und nur, wenn Posten wirklich "
            "schaden könnte.\n"
            "- Im Zweifel zwischen Politur und echtem Fehler: Ist es rechtlich/faktisch "
            "unbedenklich? -> 🟡 FREIGABE MIT HINWEISEN. Nur klare Blocker -> ⚠️ NACHBESSERN.\n"
            "- Bei Hinweisen/Nachbessern: konkret sagen WAS und WIE. Keine Wischiwaschi-Kritik.\n"
            "- Sei ehrlich – aber blockiere die Automatik nicht wegen Geschmacksfragen."
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
            "**Status:** ✅ FREIGABE | 🟡 FREIGABE MIT HINWEISEN | ⚠️ NACHBESSERN\n"
            "**Begründung:** <kurz>\n"
            "**Hinweise/Nachbesserung (falls nötig):** <konkret, oder '–'>\n\n"
            "## Markenstimme-Check\n<passt/passt nicht + warum>\n\n"
            "Nur das Markdown."
        )
