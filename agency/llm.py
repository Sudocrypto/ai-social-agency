"""Dünner Wrapper um das offizielle `anthropic` SDK.

Zentralisiert: Modellwahl, adaptives Thinking, optionales Web-Search-Tool,
Streaming bei großen max_tokens und Kosten-Logging. Kein Blackbox-Framework –
jeder Aufruf ist hier nachvollziehbar.
"""

from __future__ import annotations

from dataclasses import dataclass

import anthropic

# Preise in USD pro 1M Tokens (Stand: aktuelle Modelle).
# Nur zur groben Kostenschätzung fürs Logging – nicht abrechnungsrelevant.
PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),   # Intro-Preis ($2/$10) läuft bis 2026-08-31
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}

# Web-Search-Tool mit dynamischem Filtering (Opus 4.8 / Sonnet 5 etc.).
WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search"}

# Ab hier streamen wir, damit große Antworten keine HTTP-Timeouts riskieren.
STREAM_THRESHOLD = 8000


@dataclass
class LLMResult:
    """Ergebnis eines LLM-Aufrufs inkl. Nutzungsdaten."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    inp, out = PRICING.get(model, (0.0, 0.0))
    return (input_tokens / 1_000_000) * inp + (output_tokens / 1_000_000) * out


class LLM:
    """Wiederverwendbarer Client für alle Agents."""

    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY fehlt. Lege eine .env an (Vorlage: .env.example)."
            )
        self._client = anthropic.Anthropic(api_key=api_key)

    def call(
        self,
        *,
        system: str,
        prompt: str,
        model: str,
        max_tokens: int = 8000,
        thinking: bool = True,
        web_search: bool = False,
        effort: str = "high",
    ) -> LLMResult:
        """Ein einzelner Message-Aufruf.

        - `thinking=True` aktiviert adaptives Thinking (Modell entscheidet selbst).
        - `web_search=True` hängt das Web-Search-Tool an (Trend-Scout).
        - Streamt automatisch bei großen `max_tokens`.
        """
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        if thinking:
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["output_config"] = {"effort": effort}
        if web_search:
            kwargs["tools"] = [WEB_SEARCH_TOOL]

        message = self._collect(kwargs, max_tokens)

        text = "".join(
            block.text for block in message.content if block.type == "text"
        ).strip()

        usage = message.usage
        in_tok = usage.input_tokens
        out_tok = usage.output_tokens
        return LLMResult(
            text=text,
            model=model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=_estimate_cost(model, in_tok, out_tok),
        )

    def _collect(self, kwargs: dict, max_tokens: int):
        """Führt den Call aus – gestreamt bei großen Ausgaben, sonst direkt."""
        if max_tokens >= STREAM_THRESHOLD or "tools" in kwargs:
            with self._client.messages.stream(**kwargs) as stream:
                return stream.get_final_message()
        return self._client.messages.create(**kwargs)
