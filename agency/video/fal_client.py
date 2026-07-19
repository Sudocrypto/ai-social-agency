"""fal.ai-Aggregator-Anbindung für den Video-Producer.

fal.ai bündelt mehrere Video-Modelle. Modellwahl per Config:
  - veo-3.1          (Clips mit Ton)
  - seedance-2.0-fast (günstiges Volumen)
  - kling-3.0        (4K)

Echtes Rendern läuft NUR bei --render-video und vorhandenem FAL_KEY. Ohne das
liefert dieses Modul nur Kostenschätzungen (Dry-Run). Die Preise sind grobe
Richtwerte fürs Budget-Tracking – nicht abrechnungsverbindlich.
"""

from __future__ import annotations

# fal.ai-Endpunkt je Modell-Alias (Stand: fal.ai-Modell-IDs 2026).
MODEL_ENDPOINTS: dict[str, str] = {
    "veo-3.1": "fal-ai/veo3.1",
    "seedance-2.0-fast": "bytedance/seedance-2.0/fast/text-to-video",
    "kling-3.0": "fal-ai/kling-video/v3",
}

# Grober Kostenrichtwert in EUR pro Sekunde generiertem Video (Schätzung fürs
# Budget-Tracking). seedance-2.0-fast: ~$0.24/s laut fal-Preisliste.
PRICE_PER_SECOND_EUR: dict[str, float] = {
    "veo-3.1": 0.40,
    "seedance-2.0-fast": 0.22,
    "kling-3.0": 0.28,
}


def estimate_cost_eur(model: str, seconds: int) -> float:
    """Schätzt die Kosten eines Clips fürs Budget-Tracking (Dry-Run)."""
    return round(PRICE_PER_SECOND_EUR.get(model, 0.20) * max(1, seconds), 4)


def endpoint_for(model: str) -> str:
    if model not in MODEL_ENDPOINTS:
        raise ValueError(
            f"Unbekanntes Video-Modell '{model}'. "
            f"Erlaubt: {', '.join(MODEL_ENDPOINTS)}"
        )
    return MODEL_ENDPOINTS[model]


def build_arguments(model: str, prompt: str, seconds: int) -> dict:
    """Baut das Argument-Dict fürs jeweilige fal-Modell.

    seedance 2.0 erwartet 'duration' als String (gültig 4–15 s) und generiert
    per Default Audio – unsere KI-B-Roll ist stumm, daher generate_audio=False.
    Andere Modelle (veo etc.) bekommen die klassische numerische Dauer.
    """
    if model == "seedance-2.0-fast":
        return {
            "prompt": prompt,
            "duration": str(max(4, min(15, seconds))),
            "resolution": "720p",
            "generate_audio": False,
        }
    return {"prompt": prompt, "duration": seconds}


def render_clip(*, prompt: str, seconds: int, model: str, api_key: str) -> bytes:
    """Rendert einen Clip echt über fal.ai und gibt die .mp4-Bytes zurück.

    Wird nur bei --render-video aufgerufen. Braucht das Paket `fal-client`
    (optional, siehe requirements.txt) und einen gültigen FAL_KEY.
    """
    try:
        import fal_client  # type: ignore
    except ImportError as exc:  # pragma: no cover - nur im Render-Pfad relevant
        raise RuntimeError(
            "Paket 'fal-client' nicht installiert. Für echtes Rendern: "
            "pip install fal-client"
        ) from exc

    import os
    import urllib.request

    os.environ.setdefault("FAL_KEY", api_key)

    result = fal_client.subscribe(
        endpoint_for(model),
        arguments=build_arguments(model, prompt, seconds),
    )
    # fal liefert i.d.R. {"video": {"url": ...}} – Struktur je Modell leicht variabel.
    video = result.get("video") or result.get("videos", [{}])[0]
    url = video.get("url") if isinstance(video, dict) else None
    if not url:
        raise RuntimeError(f"Keine Video-URL in fal-Antwort: {result!r}")
    with urllib.request.urlopen(url) as resp:  # noqa: S310 - vertrauenswürdiger fal-Host
        return resp.read()
