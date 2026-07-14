"""Post-Production-Briefing – Schnittplan für mein eigenes Videomaterial.

Schneidet NICHT selbst. Liefert Cut-Liste, B-Roll-Vorschläge, Untertitel-Text,
Timing und Musik-Stimmung als Briefing für mein Schnitt-Tool.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class PostProduction(BaseAgent):
    key = "post_production"
    name = "Post-Production-Briefing"
    max_tokens = 8000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Post-Production-Planer der Agentur. Du erstellst ein "
            "Schnitt-Briefing, mit dem der Creator sein iPhone-Material + KI-B-Roll + "
            "Musik + Untertitel selbst zusammenbaut. Du schneidest nicht selbst.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- Cut-Liste mit Timing, klar an der Shotlist des Skripts orientiert.\n"
            "- B-Roll-Vorschläge markieren, wo KI-Clips reinpassen (broll_only-Modus).\n"
            "- Untertitel-Text als fertigen, sprechbaren Fließtext liefern.\n"
            "- Musik-/Stimmungshinweis pro Abschnitt. Pragmatisch, direkt umsetzbar."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        pnames = ", ".join(spec(p).name for p in platforms)
        modus = ctx.config.video.get("video_modus", "broll_only")
        return (
            f"PLATTFORMEN: {pnames}\nVIDEO-MODUS: {modus}\n\n"
            "VIDEO-SKRIPTE (vom Scriptwriter):\n"
            f"{self.prior(ctx, 'video_scriptwriter')}\n\n"
            "AUFGABE: Erstelle das Schnitt-Briefing pro Plattform als Markdown:\n\n"
            "## <Plattform>\n"
            "**Cut-Liste:**\n"
            "| # | Timecode | Inhalt | Quelle (eigenes Material / KI-B-Roll) | Übergang |\n"
            "|---|---|---|---|---|\n"
            "| 1 | 00:00–00:03 | … | … | … |\n\n"
            "**B-Roll-Vorschläge:**\n- <Szene, die als KI-Clip generiert werden soll>\n\n"
            "**Untertitel-Text:**\n<fertiger Untertitel-Fließtext>\n\n"
            "**Musik/Stimmung:**\n- <Abschnitt: Stimmung/Genre/Tempo>\n\n"
            "Nur das Markdown."
        )
