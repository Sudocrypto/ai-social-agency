"""Config-Routing und Plattform-Logik."""

from __future__ import annotations

import pytest

from agency.platforms import resolve_platforms, spec
from agency.textutils import split_by_platform


def test_model_routing_director_opus_rest_sonnet(cfg):
    assert cfg.model_for("creative_director") == cfg.models["director"]
    assert cfg.model_for("copywriter") == cfg.models["default"]
    assert cfg.model_for("trend_scout") == cfg.models["default"]


def test_model_override(cfg):
    cfg.model_overrides["copywriter"] = "claude-opus-4-8"
    assert cfg.model_for("copywriter") == "claude-opus-4-8"


def test_branded_hashtag(cfg):
    # brand_name "Danilo Takes Off" -> "#DaniloTakesOff", nicht "#DanTakesOff".
    assert cfg.branded_hashtag == "#DaniloTakesOff"


def test_ki_brand_config_loads():
    from agency.config import ROOT, load_config

    cfg = load_config(ROOT / "brand_config.ki.yaml")
    assert cfg.brand_name == "KI Kompakt"
    assert cfg.branded_hashtag == "#KIKompakt"
    assert cfg.compliance_enabled is True
    assert cfg.video.get("video_modus") == "full_synthetic"
    assert len(cfg.content_pillars) == 3


def test_branded_hashtag_in_agent_context(cfg, ctx, fake_llm):
    from agency.agents import Copywriter

    bc = Copywriter(fake_llm).brand_context(ctx)
    assert "#DaniloTakesOff" in bc
    assert "MARKEN-HASHTAG" in bc


def test_branded_hashtag_from_handle_fallback(cfg):
    cfg.brand["brand_name"] = ""
    cfg.brand["handle"] = "@danilotakesoff"
    assert cfg.branded_hashtag == "#danilotakesoff"


def test_resolve_platforms_all():
    assert resolve_platforms("all") == ["x", "instagram", "facebook", "youtube"]


def test_resolve_platforms_single():
    assert resolve_platforms("instagram") == ["instagram"]


def test_resolve_platforms_invalid():
    with pytest.raises(ValueError):
        resolve_platforms("linkedin")


def test_split_by_platform_clean():
    md = "## X (Twitter)\nA-Text\n\n## Instagram\nB-Text"
    out = split_by_platform(md, ["x", "instagram"])
    assert "A-Text" in out["x"] and "B-Text" not in out["x"]
    assert "B-Text" in out["instagram"] and "A-Text" not in out["instagram"]


def test_split_by_platform_fallback_no_headers():
    md = "kein Header hier"
    out = split_by_platform(md, ["x", "instagram"])
    assert out["x"] == md and out["instagram"] == md


def test_platform_specs_have_limits():
    for pk in ("x", "instagram", "facebook", "youtube"):
        s = spec(pk)
        assert s.max_chars > 0 and s.hashtag_count
