"""Voiceover: erzeugt eine gesprochene Tonspur aus Text.

Zwei Engines:
- 'say' : macOS-Bordmittel `say` – gratis, lokal, klingt synthetisch. Default.
- 'fal' : KI-Stimme über fal.ai – natürlicher, kostet ~Cent pro Video (nach Zeichen).

Beide liefern eine Audiodatei, die die Assembly als Tonspur unter die (stumme)
KI-B-Roll mischt.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

# Aktuelles fal-TTS-Modell (Deutsch unterstützt). Bei Bedarf hier umstellen.
FAL_TTS_ENDPOINT = "fal-ai/elevenlabs/tts/eleven-v3"


# --- macOS `say` (gratis) ----------------------------------------------------
def say_available() -> bool:
    return shutil.which("say") is not None


def build_say_command(text: str, out_path: Path | str, voice: str = "Anna") -> list[str]:
    """`say` schreibt eine AIFF-Datei, die ffmpeg direkt lesen kann."""
    return ["say", "-v", voice, "-o", str(out_path), text]


def synthesize_say(text: str, out_path: Path | str, *, voice: str = "Anna") -> Path:
    if not say_available():
        raise RuntimeError(
            "macOS-Befehl `say` nicht verfügbar (nur auf dem Mac). "
            "Für KI-Stimme: --voice-engine fal."
        )
    subprocess.run(
        build_say_command(text, out_path, voice), check=True, capture_output=True, text=True
    )
    return Path(out_path)


# --- fal.ai TTS (KI-Stimme, kostenpflichtig) ---------------------------------
def build_fal_arguments(text: str, voice: str | None = None) -> dict:
    args: dict[str, object] = {"text": text}
    if voice:
        args["voice"] = voice
    return args


def synthesize_fal(
    text: str, out_path: Path | str, *, api_key: str,
    voice: str | None = None, model: str = FAL_TTS_ENDPOINT,
) -> Path:
    try:
        import fal_client  # type: ignore
    except ImportError as exc:  # pragma: no cover - nur im echten Render-Pfad
        raise RuntimeError("Paket 'fal-client' fehlt: pip install fal-client") from exc

    os.environ.setdefault("FAL_KEY", api_key)
    result = fal_client.subscribe(model, arguments=build_fal_arguments(text, voice))
    audio = result.get("audio") or result.get("audio_url") or result.get("audio_file")
    url = audio.get("url") if isinstance(audio, dict) else audio
    if not url:
        raise RuntimeError(f"Keine Audio-URL in fal-Antwort: {result!r}")
    with urllib.request.urlopen(url) as resp:  # noqa: S310 - vertrauenswürdiger fal-Host
        Path(out_path).write_bytes(resp.read())
    return Path(out_path)


# --- gemeinsamer Einstieg -----------------------------------------------------
def synthesize(
    text: str, out_path: Path | str, *,
    engine: str = "say", voice: str | None = None, api_key: str | None = None,
) -> Path:
    """Erzeugt die Sprachdatei mit der gewählten Engine."""
    if not (text or "").strip():
        raise ValueError("Kein Text für die Sprachausgabe angegeben.")
    if engine == "say":
        return synthesize_say(text, out_path, voice=voice or "Anna")
    if engine == "fal":
        if not api_key:
            raise RuntimeError("fal-Stimme braucht einen FAL_KEY in der .env.")
        # ElevenLabs eleven-v3 ist mehrsprachig (Deutsch ok); "Aria" als Default-Timbre.
        return synthesize_fal(text, out_path, api_key=api_key, voice=voice or "Aria")
    raise ValueError(f"Unbekannte Voice-Engine '{engine}'. Erlaubt: say, fal.")
