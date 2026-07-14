"""Transparente Orchestrierung (Creative Director als Ablauf, kein Blackbox-Framework).

Führt die Agents Schritt für Schritt aus und loggt jeden Schritt, damit jeder
Zwischenstand debugbar ist.
"""

from __future__ import annotations

import sys
import time

from .base_agent import BaseAgent
from .context import RunContext
from .llm import LLM


class Pipeline:
    def __init__(self, llm: LLM, agents: list[BaseAgent]) -> None:
        self._llm = llm
        self._agents = agents

    def run(self, ctx: RunContext) -> RunContext:
        total = len(self._agents)
        for i, agent in enumerate(self._agents, start=1):
            self._log(f"[{i}/{total}] {agent.name} ({agent.key}) läuft …")
            t0 = time.monotonic()
            agent.run(ctx)
            dt = time.monotonic() - t0
            last = ctx.cost_log[-1] if ctx.cost_log else {}
            cost = last.get("cost_usd", 0.0)
            self._log(f"    fertig in {dt:.1f}s · ~${cost:.4f}")
        self._log(f"Pipeline fertig · Gesamtkosten ~${ctx.total_cost_usd:.4f}")
        return ctx

    @staticmethod
    def _log(msg: str) -> None:
        print(msg, file=sys.stderr, flush=True)
