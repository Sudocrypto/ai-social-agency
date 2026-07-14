"""Community Manager – Antwort-Vorschläge, Engagement-Fragen, CTAs."""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class CommunityManager(BaseAgent):
    key = "community_manager"
    name = "Community Manager"
    max_tokens = 5000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Community Manager der Agentur. Du hältst die Community warm: "
            "Engagement-Fragen, Antwort-Vorlagen und CTAs in der Markenstimme.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- Klingt wie ein Mensch, nicht wie ein Support-Bot.\n"
            "- Antwort-Vorlagen für typische Kommentare (positiv, skeptisch, Frage).\n"
            "- Engagement-Fragen, die echte Antworten provozieren."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        pnames = ", ".join(spec(p).name for p in platforms)
        return (
            f"PLATTFORMEN: {pnames}\n\n"
            "POST-TEXTE (Kontext):\n"
            f"{self.prior(ctx, 'copywriter', 2500)}\n\n"
            "AUFGABE: Liefere Community-Material als Markdown:\n\n"
            "## <Plattform>\n"
            "**Engagement-Frage:** <Frage>\n\n"
            "**Antwort-Vorlagen:**\n"
            "- Auf Lob: <…>\n"
            "- Auf Skepsis/Kritik: <…>\n"
            "- Auf eine typische Frage: <…>\n\n"
            "**Extra-CTA:** <…>\n\n"
            "Nur das Markdown."
        )
