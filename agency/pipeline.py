"""Transparente Orchestrierung (Creative Director als Ablauf, kein Blackbox-Framework).

Führt die Schritte nacheinander aus und loggt jeden Schritt, damit jeder
Zwischenstand debugbar ist. Ein "Schritt" ist alles mit .key/.name/.run(ctx) –
also LLM-Agents ebenso wie der Video-Producer (kein LLM).
"""

from __future__ import annotations

import sys
import time
from typing import Protocol

from .context import RunContext


class Step(Protocol):
    key: str
    name: str

    def run(self, ctx: RunContext) -> object: ...


class Pipeline:
    def __init__(self, steps: list[Step]) -> None:
        self._steps = steps

    def run(self, ctx: RunContext) -> RunContext:
        total = len(self._steps)
        for i, step in enumerate(self._steps, start=1):
            self._log(f"[{i}/{total}] {step.name} ({step.key}) läuft …")
            cost_before = len(ctx.cost_log)
            t0 = time.monotonic()
            try:
                step.run(ctx)
            except Exception as exc:  # ein Schritt darf den Lauf nicht komplett killen
                self._log(f"    ⚠️  Fehler in {step.key}: {exc}")
                continue
            dt = time.monotonic() - t0
            step_cost = sum(e["cost_usd"] for e in ctx.cost_log[cost_before:])
            extra = ""
            if step.key == "video_producer":
                extra = f" · Video ~{ctx.total_video_cost_eur:.2f}€ ({ctx.video_log and 'geplant' or 'keine Clips'})"
            self._log(f"    fertig in {dt:.1f}s · ~${step_cost:.4f}{extra}")

        self._log(
            f"Pipeline fertig · LLM ~${ctx.total_cost_usd:.4f} · "
            f"Video ~{ctx.total_video_cost_eur:.2f}€"
        )
        return ctx

    @staticmethod
    def _log(msg: str) -> None:
        print(msg, file=sys.stderr, flush=True)
