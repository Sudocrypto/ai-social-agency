"""Effort-Steuerung: Config-Auflösung + Weitergabe an die LLM-Calls."""

from __future__ import annotations

from agency.agents import Copywriter, Editor, SeoHashtag


def test_effort_default(cfg):
    # In brand_config.yaml ist default=high, copywriter ohne Override.
    assert cfg.effort_for("copywriter") == "high"


def test_effort_per_agent_override(cfg):
    assert cfg.effort_for("seo_hashtag") == "low"
    assert cfg.effort_for("community_manager") == "low"
    assert cfg.effort_for("editor") == "medium"


def test_effort_global_override_wins(cfg):
    assert cfg.effort_for("copywriter", override="low") == "low"
    assert cfg.effort_for("seo_hashtag", override="max") == "max"


def test_effort_invalid_falls_back_high(cfg):
    assert cfg.effort_for("copywriter", override="turbo") == "high"
    cfg.effort["overrides"] = {"copywriter": "bogus"}
    assert cfg.effort_for("copywriter") == "high"


def test_agent_passes_configured_effort(ctx, fake_llm):
    SeoHashtag(fake_llm).run(ctx)       # Config-Override -> low
    Copywriter(fake_llm).run(ctx)       # Default -> high
    Editor(fake_llm).run(ctx)           # Config-Override -> medium
    efforts = [c["effort"] for c in fake_llm.calls]
    assert efforts == ["low", "high", "medium"]


def test_global_override_applies_to_all(ctx, fake_llm):
    ctx.effort_override = "low"
    Copywriter(fake_llm).run(ctx)
    SeoHashtag(fake_llm).run(ctx)
    assert all(c["effort"] == "low" for c in fake_llm.calls)
