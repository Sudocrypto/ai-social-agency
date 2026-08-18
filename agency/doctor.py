"""Preflight-Check: prüft Umgebung + Config, BEVOR ein (teurer) Lauf startet.

Fängt genau die Stolpersteine ab, an denen man sonst erst mitten im Lauf
scheitert: fehlender/ungültiger API-Key, fehlendes fal-client-Paket, fehlendes
ffmpeg, unbekanntes Video-Modell. Gibt pro Punkt einen Status + konkreten
Fix-Hinweis. Rein lesend – ändert nichts, kostet nichts.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass

from .config import Config
from .video.fal_client import MODEL_ENDPOINTS

OK = "ok"
WARN = "warn"
FAIL = "fail"


@dataclass
class Check:
    """Ein einzelnes Prüfergebnis."""

    name: str
    status: str  # OK | WARN | FAIL
    detail: str
    hint: str = ""


# --- Einzelprüfungen (pur, damit testbar) ------------------------------------
def check_python(version: tuple[int, int] = sys.version_info[:2]) -> Check:
    if version >= (3, 11):
        return Check("Python", OK, f"{version[0]}.{version[1]}")
    return Check(
        "Python", FAIL, f"{version[0]}.{version[1]} (zu alt)",
        "Python 3.11+ nötig. Im venv arbeiten: source .venv/bin/activate",
    )


def check_anthropic_key(key: str | None) -> Check:
    if not key:
        return Check(
            "ANTHROPIC_API_KEY", FAIL, "fehlt",
            "In .env eintragen: ANTHROPIC_API_KEY=sk-ant-… (aus console.anthropic.com)",
        )
    if not key.startswith("sk-ant-") or len(key) < 40:
        return Check(
            "ANTHROPIC_API_KEY", FAIL, f"unplausibel (Länge {len(key)})",
            "Sieht nach Platzhalter aus – echten Key aus console.anthropic.com holen.",
        )
    return Check("ANTHROPIC_API_KEY", OK, "gesetzt, Format plausibel")


def check_fal_key(key: str | None, *, needs_video: bool) -> Check:
    if not key:
        status = WARN if needs_video else OK
        detail = "fehlt" if needs_video else "fehlt (nur für Video-Rendern nötig)"
        hint = (
            "Für echtes Video: FAL_KEY=… in .env (aus fal.ai/dashboard/keys, Format "
            "uuid:hex). Ohne Key bleibt die Pipeline im Dry-Run und schreibt nur Prompts."
            if needs_video else ""
        )
        return Check("FAL_KEY", status, detail, hint)
    if ":" not in key or len(key) < 20:
        return Check(
            "FAL_KEY", WARN, f"unplausibel (Länge {len(key)})",
            "Echter fal-Key hat das Format uuid:hex – prüfe fal.ai/dashboard/keys.",
        )
    return Check("FAL_KEY", OK, "gesetzt, Format plausibel")


def check_fal_client(importable: bool | None = None) -> Check:
    if importable is None:
        try:
            import fal_client  # type: ignore # noqa: F401
            importable = True
        except ImportError:
            importable = False
    if importable:
        return Check("fal-client (Paket)", OK, "installiert")
    return Check(
        "fal-client (Paket)", WARN, "nicht installiert",
        "Nur für echtes Rendern nötig: pip install fal-client "
        "(oder pip install -r requirements.txt).",
    )


def check_ffmpeg(available: bool | None = None) -> Check:
    if available is None:
        available = shutil.which("ffmpeg") is not None
    if available:
        return Check("ffmpeg", OK, "gefunden")
    return Check(
        "ffmpeg", WARN, "nicht gefunden",
        "Nur für Auto-Schnitt nötig: brew install ffmpeg (macOS) bzw. "
        "apt install ffmpeg (Linux). Einzelclips entstehen auch ohne.",
    )


def check_video_model(cfg: Config) -> Check:
    model = cfg.video.get("video_modell", "veo-3.1")
    if model in MODEL_ENDPOINTS:
        return Check("Video-Modell", OK, f"{model} → {MODEL_ENDPOINTS[model]}")
    return Check(
        "Video-Modell", FAIL, f"'{model}' unbekannt",
        f"Erlaubt: {', '.join(MODEL_ENDPOINTS)}. In der Config video_modell anpassen.",
    )


def check_budget(cfg: Config) -> Check:
    from .video.fal_client import estimate_cost_eur

    model = cfg.video.get("video_modell", "veo-3.1")
    secs = int(cfg.video.get("max_clip_sekunden", 6))
    budget = float(cfg.video.get("max_video_budget_eur", 5.0))
    per_clip = estimate_cost_eur(model, secs)
    clips = int(budget // per_clip) if per_clip > 0 else 0
    if clips >= 1:
        status = OK if clips >= 3 else WARN
        hint = (
            "" if clips >= 3 else
            "Für ein volleres Video max_video_budget_eur erhöhen "
            f"(z. B. {per_clip * 6:.1f} für ~6 Clips)."
        )
        return Check(
            "Video-Budget", status,
            f"~{per_clip:.2f} €/Clip ({secs}s) · Cap {budget:.2f} € → ~{clips} Clips",
            hint,
        )
    return Check(
        "Video-Budget", WARN,
        f"Cap {budget:.2f} € < {per_clip:.2f} €/Clip → 0 Clips",
        "max_video_budget_eur unter den Clip-Kosten – erhöhen, sonst rendert nichts.",
    )


def check_compliance(cfg: Config) -> Check:
    if cfg.compliance_enabled:
        rules = len(cfg.compliance.get("regeln", []) or [])
        return Check(
            "Compliance", OK,
            f"aktiv · {rules} Regeln · Marke {cfg.brand_name or '(?)'}",
        )
    return Check(
        "Compliance", WARN, "deaktiviert",
        "Für Finanz-/Werbe-Content compliance.enabled: true setzen (Rechts-Leitplanken).",
    )


# --- Gesamtlauf ---------------------------------------------------------------
def run_checks(cfg: Config, *, needs_video: bool = True) -> list[Check]:
    """Alle Prüfungen als Liste, in sinnvoller Reihenfolge."""
    return [
        check_python(),
        check_anthropic_key(cfg.anthropic_api_key),
        check_compliance(cfg),
        check_video_model(cfg),
        check_fal_key(cfg.fal_key, needs_video=needs_video),
        check_fal_client(),
        check_ffmpeg(),
        check_budget(cfg),
    ]


def worst_status(checks: list[Check]) -> str:
    if any(c.status == FAIL for c in checks):
        return FAIL
    if any(c.status == WARN for c in checks):
        return WARN
    return OK
