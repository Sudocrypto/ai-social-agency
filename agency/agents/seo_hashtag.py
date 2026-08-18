"""SEO/Hashtag-Spezialist – Titel, Descriptions, Keywords, Hashtag-Sets.

Ausgabe pro Plattform in klar gelabelten Feldern, damit meta.json maschinell
befüllt werden kann.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class SeoHashtag(BaseAgent):
    key = "seo_hashtag"
    name = "SEO/Hashtag-Spezialist"
    max_tokens = 6000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der SEO- und Hashtag-Spezialist der Agentur. Du optimierst auf "
            "Auffindbarkeit pro Plattform, ohne unnatürlich oder spammy zu wirken.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- Titel/Description plattformgerecht (YouTube-SEO ≠ Instagram-Caption).\n"
            "- Hashtag-Mengen an die Plattform-Vorgabe halten, Mix aus groß/nischig.\n"
            "- Keywords: echte Suchbegriffe der Zielgruppe zum Thema Auswandern.\n"
            "- Nutze ETABLIERTE, korrekt geschriebene Hashtags – keine erfundenen "
            "oder verdrehten (z.B. #DigitalNomad statt #DigitalNomade).\n"
            "- Setze den Marken-Hashtag IMMER exakt wie oben vorgegeben; erfinde "
            "keine Abkürzung der Marke.\n"
            "- Exakt die geforderten Feld-Labels benutzen (werden maschinell geparst)."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        briefs = "\n".join(
            f"### {spec(p).name} (Hashtags: {spec(p).hashtag_count})" for p in platforms
        )
        thema = ctx.topic or ctx.pillar
        return (
            f"THEMA: {thema}\nPILLAR: {ctx.pillar}\n\n"
            "POST-TEXTE (Kontext):\n"
            f"{self.prior(ctx, 'copywriter', 2500)}\n\n"
            "AUFGABE: Liefere pro Plattform SEO-Felder als Markdown mit GENAU diesen Labels:\n\n"
            "## <Plattform>\n"
            "**Titel:** <Titel>\n"
            "**Description:** <1–3 Sätze>\n"
            "**Keywords:** <komma, getrennt>\n"
            "**Hashtags:** <#hashtag #hashtag …>\n\n"
            f"Plattformen:\n{briefs}\n\n"
            "Nur das Markdown, exakt diese Feld-Labels."
        )
