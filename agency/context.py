"""RunContext: transportiert Ziel, Marke und alle Zwischenergebnisse durch die Pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .config import Config


@dataclass
class RunContext:
    """Zustand eines einzelnen Pipeline-Durchlaufs.

    Jeder Agent liest, was er braucht, aus `outputs` (die Ergebnisse der
    Vorgänger) und schreibt sein eigenes Ergebnis unter seinem Schlüssel zurück.
    """

    config: Config
    pillar: str
    platform: str          # "x" | "instagram" | "facebook" | "youtube" | "all"
    count: int
    topic: str | None = None
    websearch: bool = True
    run_date: str = field(default_factory=lambda: date.today().isoformat())

    # Ergebnisse: agent_key -> beliebiges Ergebnis (meist Text/Markdown oder dict).
    outputs: dict[str, object] = field(default_factory=dict)
    # Kosten-Log: Liste von {agent, model, input_tokens, output_tokens, cost_usd}.
    cost_log: list[dict] = field(default_factory=list)

    def set(self, agent_key: str, value: object) -> None:
        self.outputs[agent_key] = value

    def get(self, agent_key: str, default: object = None) -> object:
        return self.outputs.get(agent_key, default)

    def record_cost(self, agent_key: str, model: str, in_tok: int, out_tok: int, cost: float) -> None:
        self.cost_log.append(
            {
                "agent": agent_key,
                "model": model,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cost_usd": round(cost, 5),
            }
        )

    @property
    def total_cost_usd(self) -> float:
        return round(sum(entry["cost_usd"] for entry in self.cost_log), 5)
