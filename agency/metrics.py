"""Lädt gelieferte Performance-Daten (CSV/JSON) für den Growth-Analysten.

Ziel: reale Zahlen (Impressions, Likes, Watchtime …) in eine kompakte,
LLM-lesbare Übersicht bringen – inkl. einfacher Aggregate pro Plattform –,
damit die Optimierungsvorschläge datengetrieben statt geraten sind.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

# Spaltennamen, die als Plattform-Dimension gelten.
_PLATFORM_COLS = {"platform", "plattform"}


@dataclass
class Metrics:
    rows: list[dict]
    source: str

    @classmethod
    def load(cls, path: Path | str) -> "Metrics":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Metrics-Datei nicht gefunden: {path}")
        suffix = path.suffix.lower()
        if suffix == ".json":
            rows = cls._load_json(path)
        elif suffix in (".csv", ".tsv"):
            rows = cls._load_csv(path, delimiter="\t" if suffix == ".tsv" else ",")
        else:
            raise ValueError(f"Nicht unterstütztes Format '{suffix}'. Nutze .csv/.tsv/.json.")
        if not rows:
            raise ValueError(f"Keine Daten in {path}.")
        return cls(rows=rows, source=str(path))

    @staticmethod
    def _load_json(path: Path) -> list[dict]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            # {"plattform": {...}} oder flache Kennzahlen -> in Zeilen wandeln.
            if all(isinstance(v, dict) for v in data.values()):
                return [{"plattform": k, **v} for k, v in data.items()]
            return [data]
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
        raise ValueError("JSON muss ein Objekt oder eine Liste von Objekten sein.")

    @staticmethod
    def _load_csv(path: Path, delimiter: str) -> list[dict]:
        with path.open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh, delimiter=delimiter))

    # --- Darstellung ---------------------------------------------------------
    def _platform_key(self) -> str | None:
        keys = {k.lower(): k for k in (self.rows[0].keys() if self.rows else [])}
        for cand in _PLATFORM_COLS:
            if cand in keys:
                return keys[cand]
        return None

    @staticmethod
    def _as_number(val) -> float | None:
        try:
            return float(str(val).replace(",", "").replace("%", "").strip())
        except (ValueError, AttributeError):
            return None

    def aggregates(self) -> dict[str, dict[str, float]]:
        """Summen je numerischer Spalte, gruppiert nach Plattform (falls vorhanden)."""
        pcol = self._platform_key()
        if not pcol:
            return {}
        numeric_cols = [
            c for c in self.rows[0]
            if c != pcol and any(self._as_number(r.get(c)) is not None for r in self.rows)
        ]
        out: dict[str, dict[str, float]] = {}
        for r in self.rows:
            plat = str(r.get(pcol, "?"))
            bucket = out.setdefault(plat, {})
            for c in numeric_cols:
                n = self._as_number(r.get(c))
                if n is not None:
                    bucket[c] = round(bucket.get(c, 0.0) + n, 3)
        return out

    def to_markdown(self, max_rows: int = 50) -> str:
        cols = list(self.rows[0].keys())
        lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for r in self.rows[:max_rows]:
            lines.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
        if len(self.rows) > max_rows:
            lines.append(f"| …({len(self.rows) - max_rows} weitere Zeilen)… |")

        agg = self.aggregates()
        if agg:
            lines.append("")
            lines.append("**Summen pro Plattform:**")
            for plat, vals in agg.items():
                pretty = ", ".join(f"{k}={v:g}" for k, v in vals.items())
                lines.append(f"- {plat}: {pretty}")
        return "\n".join(lines)
