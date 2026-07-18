"""Automatik-Bausteine: Freigabe-Gate, Auto-Schnittplan, Pipeline-Fabrik – offline."""

from __future__ import annotations

from agency.app import build_pipeline
from agency.assembly.scaffold import auto_plan
from agency.publishing.approval import gate_status


def _day(tmp_path, director, compliance=None):
    day = tmp_path / "2026-07-20"
    (day / "youtube").mkdir(parents=True)
    (day / "youtube" / "post.md").write_text("## youtube\n### Post 1\nText.", encoding="utf-8")
    (day / "director_review.md").write_text(
        f"# Freigabe\n### YouTube\n**Status:** {director}\n", encoding="utf-8"
    )
    if compliance:
        (day / "compliance_report.md").write_text(
            f"# Compliance\n### YouTube\n**Status:** {compliance}\n", encoding="utf-8"
        )
    return day


def test_gate_allows_when_clear(tmp_path):
    day = _day(tmp_path, "✅ FREIGABE", "✅ OK")
    g = gate_status(day, "youtube")
    assert g["allowed"] is True and g["reason"] == "frei"


def test_gate_blocks_on_director(tmp_path):
    day = _day(tmp_path, "⚠️ NACHBESSERN", "✅ OK")
    g = gate_status(day, "youtube")
    assert g["allowed"] is False and "NACHBESSERN" in g["reason"]


def test_gate_blocks_on_compliance(tmp_path):
    day = _day(tmp_path, "✅ FREIGABE", "⚠️ RISIKO")
    g = gate_status(day, "youtube")
    assert g["allowed"] is False and "RISIKO" in g["reason"]


def test_gate_allows_when_no_verdict(tmp_path):
    day = tmp_path / "2026-07-20"
    (day / "youtube").mkdir(parents=True)
    g = gate_status(day, "youtube")
    assert g["allowed"] is True  # kein Urteil -> nicht blockiert


def test_auto_plan_from_rendered_clips(tmp_path):
    day = tmp_path / "2026-07-20"
    broll = day / "youtube" / "broll"
    broll.mkdir(parents=True)
    (broll / "clip_01.mp4").write_bytes(b"x")
    (broll / "clip_02.mp4").write_bytes(b"x")
    (day / "youtube" / "post_production.md").write_text(
        "**Untertitel-Text:**\nSatz eins. Satz zwei.\n", encoding="utf-8"
    )
    plan = auto_plan(day, "youtube")
    assert plan is not None
    assert len(plan.segments) == 2
    assert all(s.mute for s in plan.segments)  # KI-B-Roll stumm
    assert plan.width == 1920 and plan.height == 1080
    assert plan.music is None  # ohne --music kein Track


def test_auto_plan_none_without_clips(tmp_path):
    day = tmp_path / "2026-07-20"
    (day / "youtube").mkdir(parents=True)
    assert auto_plan(day, "youtube") is None


def test_build_pipeline_shape():
    pipe = build_pipeline(llm=None)
    keys = [s.key for s in pipe._steps]
    assert keys[0] == "trend_scout" and keys[-1] == "creative_director"
    assert "compliance_officer" in keys and len(keys) == 14
