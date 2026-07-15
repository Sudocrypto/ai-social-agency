"""Config-Loading: liest .env (API-Keys) + brand_config.yaml (Marke/Modelle).

Keys werden NIE hardcoded – immer aus der Umgebung/`.env`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Projekt-Root = eine Ebene über diesem Package.
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT / "brand_config.yaml"


@dataclass
class Config:
    """Gebündelte Laufzeit-Konfiguration für die gesamte Pipeline."""

    brand: dict[str, Any]
    models: dict[str, str]
    model_overrides: dict[str, str]
    video: dict[str, Any]
    effort: dict[str, Any]
    websearch_default: bool
    anthropic_api_key: str | None
    fal_key: str | None
    raw: dict[str, Any] = field(repr=False)

    #: Erlaubte Effort-Stufen (steuern Denk-Tiefe -> Kosten/Qualität).
    VALID_EFFORT = ("low", "medium", "high", "xhigh", "max")

    # --- Modellwahl pro Agent -------------------------------------------------
    def model_for(self, agent_key: str) -> str:
        """Modell-ID für einen Agent.

        Priorität: explizites model_override > 'director' für den Director >
        globaler default.
        """
        if agent_key in self.model_overrides:
            return self.model_overrides[agent_key]
        if agent_key == "creative_director":
            return self.models.get("director", "claude-opus-4-8")
        return self.models.get("default", "claude-sonnet-5")

    # --- Effort pro Agent -----------------------------------------------------
    def effort_for(self, agent_key: str, override: str | None = None) -> str:
        """Effort-Stufe für einen Agent.

        Priorität: globaler CLI-Override > per-Agent-Override aus der Config >
        globaler Default. Ungültige Werte fallen sicher auf 'high' zurück.
        """
        if override:
            return override if override in self.VALID_EFFORT else "high"
        overrides = self.effort.get("overrides", {}) or {}
        value = overrides.get(agent_key, self.effort.get("default", "high"))
        return value if value in self.VALID_EFFORT else "high"

    # --- Bequeme Zugriffe auf Marken-Felder ----------------------------------
    @property
    def brand_name(self) -> str:
        return self.brand.get("brand_name", "")

    @property
    def content_pillars(self) -> list[str]:
        return list(self.brand.get("content_pillars", []))

    @property
    def branded_hashtag(self) -> str:
        """Der einzig korrekte Marken-Hashtag, aus brand_name (sonst handle)."""
        name = str(self.brand.get("brand_name", "")).strip()
        if name:
            return "#" + "".join(name.split())          # "Danilo Takes Off" -> "#DaniloTakesOff"
        handle = str(self.brand.get("handle", "")).lstrip("@").strip()
        return f"#{handle}" if handle else ""


def load_config(config_path: Path | str = DEFAULT_CONFIG_PATH) -> Config:
    """Lädt .env + brand_config.yaml und validiert das Nötigste."""
    load_dotenv(ROOT / ".env")  # still, falls nicht vorhanden

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"brand_config.yaml nicht gefunden: {path}. "
            "Lege sie im Projekt-Root an (Vorlage im Repo)."
        )
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    models = data.get("models", {}) or {}
    video = data.get("video", {}) or {}
    # Video-Felder liegen in der Vorlage teils top-level -> zusammenführen.
    for key in ("video_modus", "video_modell", "max_clip_sekunden", "max_video_budget_eur"):
        if key in data:
            video.setdefault(key, data[key])

    return Config(
        brand=data,
        models=models,
        model_overrides=data.get("model_overrides", {}) or {},
        video=video,
        effort=data.get("effort", {}) or {},
        websearch_default=bool(data.get("websearch_default", True)),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        fal_key=os.environ.get("FAL_KEY"),
        raw=data,
    )
