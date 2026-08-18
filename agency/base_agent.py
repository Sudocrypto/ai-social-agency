"""Basisklasse für alle "Mitarbeiter" (Agents).

Jeder Agent = eigene Klasse mit eigenem System-Prompt und klarer Rolle.
Die Basisklasse übernimmt Modellwahl, LLM-Aufruf und Kosten-Logging, damit die
konkreten Agents sich nur um ihren Prompt und ihr Ergebnis kümmern.
"""

from __future__ import annotations

from .context import RunContext
from .llm import LLM


class BaseAgent:
    """Gemeinsame Mechanik aller Agents."""

    #: Eindeutiger Schlüssel (für outputs, Kosten-Log, Modell-Overrides).
    key: str = "base"
    #: Menschlicher Name/Rolle für Logs und Review.
    name: str = "Agent"
    #: max_tokens für die Ausgabe dieses Agents.
    max_tokens: int = 8000
    #: Trend-Scout überschreibt das auf True.
    uses_web_search: bool = False

    def __init__(self, llm: LLM) -> None:
        self._llm = llm

    # --- von Unterklassen zu überschreiben -----------------------------------
    def system_prompt(self, ctx: RunContext) -> str:
        """Rollenbeschreibung + Markenstimme. Muss überschrieben werden."""
        raise NotImplementedError

    def build_prompt(self, ctx: RunContext) -> str:
        """Konkrete Arbeitsanweisung inkl. relevanter Vorgänger-Ergebnisse."""
        raise NotImplementedError

    def parse(self, ctx: RunContext, text: str) -> object:
        """Roh-Text in ein Ergebnis umwandeln. Default: Text unverändert."""
        return text

    # --- Standard-Ablauf ------------------------------------------------------
    def run(self, ctx: RunContext) -> object:
        model = ctx.config.model_for(self.key)
        effort = ctx.config.effort_for(self.key, ctx.effort_override)
        result = self._llm.call(
            system=self.system_prompt(ctx),
            prompt=self.build_prompt(ctx),
            model=model,
            max_tokens=self.max_tokens,
            web_search=self.uses_web_search and ctx.websearch,
            effort=effort,
        )
        ctx.record_cost(
            self.key, result.model, result.input_tokens, result.output_tokens, result.cost_usd
        )
        parsed = self.parse(ctx, result.text)
        ctx.set(self.key, parsed)
        return parsed

    # --- Zugriff auf Vorgänger-Ergebnisse ------------------------------------
    def prior(self, ctx: RunContext, agent_key: str, limit: int = 4000) -> str:
        """Ergebnis eines vorherigen Agents als (ggf. gekürzter) String."""
        val = ctx.get(agent_key, "")
        text = val if isinstance(val, str) else str(val)
        if len(text) > limit:
            return text[:limit] + "\n…(gekürzt)…"
        return text

    # --- gemeinsamer Marken-Kontext für System-Prompts ------------------------
    def brand_context(self, ctx: RunContext) -> str:
        b = ctx.config.brand
        pillars = "\n".join(f"  - {p}" for p in ctx.config.content_pillars)
        base = (
            f"MARKE / KANAL: {b.get('brand_name', '')} ({b.get('handle', '')})\n"
            f"MARKEN-HASHTAG (immer exakt so schreiben, niemals abkürzen oder abwandeln): "
            f"{ctx.config.branded_hashtag}\n"
            f"WICHTIG: Der Marken-Hashtag ist ein HASHTAG zum Taggen/zur Auffindbarkeit, "
            f"KEIN Kanal. 'Abonnieren'/'Folgen'-CTAs beziehen sich auf den Kanal bzw. das "
            f"Handle {b.get('handle', '')} – niemals 'folge dem Hashtag'.\n"
            f"THEMA: {b.get('thema', '')}\n"
            f"SPRACHE/STIL: {b.get('sprache', '')}\n"
            f"TONALITÄT: {b.get('tonalität', '')}\n"
            f"ZIELGRUPPE: {b.get('zielgruppe', '')}\n"
            f"CONTENT-PILLARS:\n{pillars}"
        )
        compliance = ctx.config.compliance_block()
        return f"{base}\n\n{compliance}" if compliance else base
