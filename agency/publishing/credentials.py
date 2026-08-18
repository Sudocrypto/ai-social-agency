"""Lädt Plattform-Zugangsdaten aus der Umgebung/.env – nie hardcoded."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from ..config import ROOT
from .registry import PUBLISHERS

# Alle von irgendeinem Publisher benötigten Env-Variablen.
ALL_ENV_KEYS: list[str] = sorted(
    {k for pub in PUBLISHERS.values() for k in pub.required_env}
)


def load_credentials() -> dict[str, str | None]:
    """Liest alle Publishing-Env-Variablen (aus .env + Umgebung)."""
    load_dotenv(ROOT / ".env")
    return {k: os.environ.get(k) for k in ALL_ENV_KEYS}


def platform_ready(platform_key: str, creds: dict[str, str | None]) -> tuple[bool, list[str]]:
    """(bereit?, fehlende_variablen) für echtes Posten auf einer Plattform."""
    pub = PUBLISHERS[platform_key]
    missing = pub.missing_env(creds)
    return (not missing, missing)
