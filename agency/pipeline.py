"""Transparente Orchestrierung (Creative Director als Ablauf, kein Blackbox-Framework).

Standard: sequenziell – jeder Schritt einzeln geloggt, maximal debugbar.
Opt-in (parallel=True): unabhängige Schritte einer Abhängigkeits-Ebene laufen
gleichzeitig (I/O-gebundene LLM-Calls -> schneller). Ergebnis ist identisch.

Ein "Schritt" ist alles mit .key/.name/.run(ctx) – LLM-Agents wie der
Video-Producer (kein LLM).
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Protocol

from .context import RunContext
from .graph import DEPENDENCIES, compute_levels


class Step(Protocol):
    key: str
    name: str

    def run(self, ctx: RunContext) -> object: ...


class Pipeline:
    def __init__(
        self, steps: list[Step], *, parallel: bool = False,
        deps: dict[str, list[str]] | None = None,
    ) -> None:
        self._steps = steps
        self._parallel = parallel
        self._deps = deps if deps is not None else DEPENDENCIES

    def run(self, ctx: RunContext) -> RunContext:
        if self._parallel:
            self._run_parallel(ctx)
        else:
            self._run_sequential(ctx)
        self._log(
            f"Pipeline fertig · LLM ~${ctx.total_cost_usd:.4f} · "
            f"Video ~{ctx.total_video_cost_eur:.2f}€"
        )
        return ctx

    # --- sequenziell (Default) -----------------------------------------------
    def _run_sequential(self, ctx: RunContext) -> None:
        total = len(self._steps)
        for i, step in enumerate(self._steps, start=1):
            self._log(f"[{i}/{total}] {step.name} ({step.key}) läuft …")
            before = len(ctx.cost_log)
            t0 = time.monotonic()
            self._safe_run(step, ctx)
            dt = time.monotonic() - t0
            step_cost = sum(e["cost_usd"] for e in ctx.cost_log[before:])
            self._log(f"    fertig in {dt:.1f}s · ~${step_cost:.4f}")

    # --- parallel (opt-in) ---------------------------------------------------
    def _run_parallel(self, ctx: RunContext) -> None:
        by_key = {s.key: s for s in self._steps}
        levels = compute_levels([s.key for s in self._steps], self._deps)
        for n, level in enumerate(levels, start=1):
            names = ", ".join(by_key[k].name for k in level)
            self._log(f"[Ebene {n}/{len(levels)}] parallel: {names}")
            t0 = time.monotonic()
            if len(level) == 1:
                self._safe_run(by_key[level[0]], ctx)
            else:
                with ThreadPoolExecutor(max_workers=len(level)) as pool:
                    list(pool.map(lambda k: self._safe_run(by_key[k], ctx), level))
            self._log(f"    Ebene fertig in {time.monotonic() - t0:.1f}s")

    # --- gemeinsam -----------------------------------------------------------
    def _safe_run(self, step: Step, ctx: RunContext) -> None:
        try:
            step.run(ctx)
        except Exception as exc:  # ein Schritt darf den Lauf nicht komplett killen
            ctx.record_error(step.key, str(exc))
            self._log(f"    ⚠️  Fehler in {step.key}: {exc}")

    @staticmethod
    def _log(msg: str) -> None:
        print(msg, file=sys.stderr, flush=True)
