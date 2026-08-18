"""Protokolliert tatsächlich veröffentlichte Posts (für Dashboard & Nachverfolgung)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..config import ROOT

POST_LOG = ROOT / "monitoring" / "post_log.json"


def load_post_log(store: Path | str = POST_LOG) -> list[dict]:
    p = Path(store)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def record_post(
    platform: str, url: str | None, package_date: str,
    *, when: str | None = None, store: Path | str = POST_LOG,
) -> dict:
    """Hängt einen veröffentlichten Post ans Log an."""
    p = Path(store)
    log = load_post_log(p)
    entry = {
        "platform": platform,
        "url": url or "",
        "package_date": package_date,
        "when": when or datetime.now().isoformat(timespec="seconds"),
    }
    log.append(entry)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry
