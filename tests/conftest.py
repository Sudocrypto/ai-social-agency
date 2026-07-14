"""Gemeinsame Test-Fixtures: Stub-LLM + Pipeline-Bausteine, komplett offline."""

from __future__ import annotations

import pytest

from agency.config import load_config
from agency.context import RunContext
from agency.llm import LLMResult, _estimate_cost
from agency.output_writer import OUTPUT_ROOT  # noqa: F401 (Referenz für Monkeypatch-Ziel)

PLATFORMS = [
    ("X (Twitter)", "x"),
    ("Instagram", "instagram"),
    ("Facebook", "facebook"),
    ("YouTube", "youtube"),
]


def _per_platform(body_fn) -> str:
    return "\n\n".join(f"## {name}\n{body_fn(name)}" for name, _ in PLATFORMS)


class FakeLLM:
    """Ersetzt den echten anthropic-Client. Antwortet je nach Agent-Rolle
    (erkannt am System-Prompt) mit plausiblem, parsebarem Markdown."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def call(self, *, system, prompt, model, max_tokens, web_search=False, effort="high"):
        self.calls.append(
            {"model": model, "web_search": web_search, "system": system, "prompt": prompt}
        )
        s = system
        if "Trend-Scout" in s:
            body = "## Aktuelle Trends & Formate\n- Ort-Reveal-Clips"
        elif "Content-Stratege" in s:
            body = "## Kern-Angle\nEhrlicher erster Monat."
        elif "Copywriter" in s:
            body = _per_platform(
                lambda n: f"### Post 1\n**Hook:** {n}-Hook\n\n**Text:**\nRoh {n}.\n\n"
                f"**CTA:** Folge.\n\n**Hashtags:** #auswandern"
            )
        elif "Video-Scriptwriter" in s:
            body = _per_platform(lambda n: f"**Hook (0–3 Sek.):** {n}\n\n**Skript:**\nText.")
        elif "Post-Production" in s:
            body = _per_platform(lambda n: "**Cut-Liste:**\n| 1 | 00:00 | Intro | eigenes | hart |")
        elif "Visual Designer" in s:
            body = _per_platform(
                lambda n: "**Video-Prompts (B-Roll):**\n"
                f"- VIDEO-PROMPT [8s]: cinematic shot for {n}"
            )
        elif "Hashtag-Spezialist" in s:
            body = _per_platform(
                lambda n: f"**Titel:** {n}-Titel\n**Description:** Kurz.\n"
                "**Keywords:** auswandern, thailand\n**Hashtags:** #auswandern #reise"
            )
        elif "Community Manager" in s:
            body = _per_platform(lambda n: "**Engagement-Frage:** Wohin?")
        elif "Lektor" in s:
            body = _per_platform(
                lambda n: f"### Post 1\n**Hook:** {n}-Hook\n\n**Text:**\nKorrigiert {n}.\n\n"
                f"**CTA:** Folge.\n\n**Hashtags:** #auswandern"
            )
        elif "Publisher" in s:
            body = _per_platform(lambda n: f"### Post 1\nFinaler {n}-Post. #auswandern #reise")
        elif "Growth-Analyst" in s:
            body = "## KPIs pro Plattform\n### X\n- Saves"
        elif "Creative Director" in s:
            body = "## Gesamturteil\nStark.\n\n### X\n**Status:** ✅ FREIGABE"
        else:
            body = "## X\nleer"
        return LLMResult(
            text=body, model=model, input_tokens=500, output_tokens=400,
            cost_usd=_estimate_cost(model, 500, 400),
        )


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def cfg():
    return load_config()


@pytest.fixture
def ctx(cfg):
    return RunContext(
        config=cfg, pillar=cfg.content_pillars[0], platform="all", count=1,
        topic="Erster Monat Thailand", websearch=True, render_video=False,
    )


@pytest.fixture
def tmp_output(monkeypatch, tmp_path):
    """Lenkt write_package auf ein temporäres Verzeichnis um."""
    import agency.output_writer as ow

    monkeypatch.setattr(ow, "OUTPUT_ROOT", tmp_path)
    return tmp_path
