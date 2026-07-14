"""Lektor/Editor – prüft alle Texte und korrigiert direkt.

Nimmt die Post-Texte des Copywriters, korrigiert Rechtschreibung, Grammatik,
Konsistenz und Markenstimme und gibt die bereinigte, gleiche Struktur zurück.
Ergebnis geht an den Publisher (post.md).
"""

from __future__ import annotations

from ..base_agent import BaseAgent
from ..context import RunContext


class Editor(BaseAgent):
    key = "editor"
    name = "Lektor/Editor"
    max_tokens = 8000

    def system_prompt(self, ctx: RunContext) -> str:
        return (
            "Du bist der Lektor der Agentur – die letzte Instanz vor dem Publisher. "
            "Du korrigierst Rechtschreibung, Grammatik, Zeichensetzung und glättest "
            "Formulierungen, OHNE die Aussage oder Struktur zu verändern.\n\n"
            f"{self.brand_context(ctx)}\n\n"
            "Regeln:\n"
            "- Korrigiere direkt im Text. Behalte die exakte Markdown-Struktur bei "
            "(## Plattform / ### Post / **Hook** / **Text** / **CTA** / **Hashtags**).\n"
            "- Wahre die Markenstimme (locker, direkt, Ich-Perspektive) – kein Glattbügeln "
            "zu Corporate.\n"
            "- Keine Kommentare, keine Erklärungen – gib NUR den korrigierten Text zurück."
        )

    def build_prompt(self, ctx: RunContext) -> str:
        return (
            "AUFGABE: Korrigiere die folgenden Post-Texte und gib sie in identischer "
            "Markdown-Struktur bereinigt zurück:\n\n"
            f"{self.prior(ctx, 'copywriter', 12000)}\n\n"
            "Nur der korrigierte Text."
        )
