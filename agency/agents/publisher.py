"""Publisher/Platform-Adapter – formatiert freigegebenen Content pro Plattform.

Nimmt die lektorierten Post-Texte + SEO-Hashtags und baut den final postbaren
Text exakt nach den Specs jeder Plattform. Ergebnis wird als post.md geschrieben.
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext
from ..platforms import resolve_platforms, spec


class Publisher(BaseAgent):
    key = "publisher"
    name = "Publisher/Platform-Adapter"
    max_tokens = 8000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Publisher/Platform-Adapter der Agentur. Du bringst den finalen "
            "Text in exakt die Form, die auf jeder Plattform direkt postbar ist.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- Halte Zeichenlimits und Hashtag-Mengen der Plattform strikt ein.\n"
            "- Setze die vom SEO gelieferten Hashtags korrekt und plattformgerecht.\n"
            "- X: ggf. sauber nummerierter Thread. Instagram: Caption + Hashtag-Block.\n"
            "- Der Text muss copy-paste-fertig sein – keine Meta-Kommentare."
        )

    def _briefs(self, platforms: list[str]) -> str:
        out = []
        for p in platforms:
            s = spec(p)
            out.append(
                f"### {s.name}\n- max. ~{s.max_chars} Zeichen · Hashtags: {s.hashtag_count}\n"
                f"- Format: {s.format_hint}"
            )
        return "\n".join(out)

    def build_prompt(self, ctx: RunContext) -> str:
        platforms = resolve_platforms(ctx.platform)
        # Lektorierte Fassung bevorzugen, sonst Rohtext des Copywriters.
        copy = self.prior(ctx, "editor", 12000) or self.prior(ctx, "copywriter", 12000)
        return (
            "LEKTORIERTE POST-TEXTE:\n"
            f"{copy}\n\n"
            "SEO-HASHTAGS/KEYWORDS:\n"
            f"{self.prior(ctx, 'seo_hashtag', 3000)}\n\n"
            "PLATTFORM-VORGABEN:\n"
            f"{self._briefs(platforms)}\n\n"
            "AUFGABE: Erzeuge den finalen, copy-paste-fertigen Post pro Plattform als "
            "Markdown mit dieser Struktur:\n\n"
            "## <Plattform>\n"
            "### Post 1\n<fertiger Text inkl. Hashtags an der richtigen Stelle>\n\n"
            "(weitere Varianten als ### Post 2 …)\n\n"
            "Nur das Markdown."
        )
