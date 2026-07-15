"""Compliance-Prüfer – juristische Absicherung von finanzbezogenem Content.

Prüft die finalen Posts gegen die Compliance-Regeln der Marke und flaggt riskante
Formulierungen (konkrete Anlageberatung, garantierte Renditen, FOMO, fehlende
Kennzeichnung), BEVOR der Creative Director freigibt. Läuft nur im
Compliance-Modus (compliance.enabled). Ersetzt keine Rechtsberatung.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class ComplianceOfficer(BaseAgent):
    key = "compliance_officer"
    name = "Compliance-Prüfer"
    max_tokens = 6000

    def run(self, ctx: RunContext) -> object:
        # Nur aktiv, wenn die Marke im Compliance-Modus läuft.
        if not ctx.config.compliance_enabled:
            return None
        return super().run(ctx)

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Compliance-Prüfer der Agentur – die juristische "
            "Absicherungs-Instanz für finanzbezogenen Content. Du bist streng und "
            "vorsichtig: Im Zweifel flaggst du.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Deine Aufgabe: Prüfe die finalen Posts gegen die oben genannten "
            "COMPLIANCE-Regeln und auf typische rechtliche Fallstricke bei "
            "Finanz-/Krypto-Content:\n"
            "- konkrete Kauf-/Verkaufsempfehlungen oder Preisziele als Gewissheit\n"
            "- garantierte Renditen, 'sicherer Gewinn', 'schnell reich'\n"
            "- Beratungs-Ton statt Meinung/Bildung/Unterhaltung\n"
            "- FOMO/Dringlichkeit ('nur heute', 'letzte Chance')\n"
            "- fehlende Kennzeichnung von Werbung/Affiliate\n"
            "- unbelegte Zahlen/Behauptungen, Kursmanipulation\n\n"
            "Du bist kein Anwalt und triffst keine endgültige Rechtsentscheidung – "
            "du reduzierst Risiko und machst konkret auf Probleme aufmerksam."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        pnames = ", ".join(spec(p).name for p in platforms)
        rules = "\n".join(f"- {r}" for r in ctx.config.compliance_rules)
        return (
            f"PLATTFORMEN: {pnames}\n\n"
            "ZU PRÜFENDE FINALE POSTS (Publisher):\n"
            f"{self.prior(ctx, 'publisher', 6000)}\n\n"
            f"COMPLIANCE-REGELN DER MARKE:\n{rules}\n\n"
            "(Hinweis: Ein rechtlicher Disclaimer wird automatisch an jeden Post "
            "angehängt – prüfe den eigentlichen Text, nicht das Fehlen des Disclaimers.)\n\n"
            "AUSGABE als Markdown:\n\n"
            "## Gesamt-Risikoeinschätzung\n<1–2 Sätze>\n\n"
            "## Prüfung pro Plattform\n"
            "### <Plattform>\n"
            "**Status:** ✅ OK | ⚠️ RISIKO\n"
            "**Gefundene Risiken:** <konkret, mit Zitat; oder 'keine'>\n"
            "**Korrektur-Vorschlag:** <konkret umformulieren, falls Risiko>\n\n"
            "## Empfehlung an den Creative Director\n<freigeben / nachbessern + warum>\n\n"
            "Nur das Markdown."
        )
