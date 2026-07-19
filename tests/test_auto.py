"""Automatik-Bausteine: Freigabe-Gate, Auto-Schnittplan, Pipeline-Fabrik – offline."""

from __future__ import annotations

import auto
from agency.app import build_pipeline
from agency.assembly.scaffold import auto_plan
from agency.publishing.approval import gate_status


def test_context_records_and_flags_credit_error(cfg):
    from agency.context import RunContext

    ctx = RunContext(config=cfg, pillar="tools", platform="youtube", count=1)
    ctx.record_error("trend_scout", "Error code: 400 - Your credit balance is too low")
    assert ctx.errors and ctx.errors[0]["agent"] == "trend_scout"
    assert ctx.credit_error is True


def test_context_credit_error_false_for_other_errors(cfg):
    from agency.context import RunContext

    ctx = RunContext(config=cfg, pillar="tools", platform="youtube", count=1)
    ctx.record_error("copywriter", "irgendein Timeout")
    assert ctx.credit_error is False


def test_pipeline_records_step_errors(cfg):
    from agency.context import RunContext
    from agency.pipeline import Pipeline

    class Boom:
        key = "boom"
        name = "Boom"

        def run(self, ctx):
            raise RuntimeError("kaputt")

    ctx = RunContext(config=cfg, pillar="tools", platform="youtube", count=1)
    Pipeline([Boom()]).run(ctx)
    assert any(e["agent"] == "boom" and "kaputt" in e["message"] for e in ctx.errors)


def test_cost_override_flags_parse():
    args = auto.build_parser().parse_args(
        ["--pillar", "tools", "--max-budget", "1.0", "--max-clip-seconds", "4"]
    )
    assert args.max_budget == 1.0 and args.max_clip_seconds == 4
    # Ohne Flags bleiben die Overrides None -> Config gilt unverändert.
    d = auto.build_parser().parse_args(["--pillar", "tools"])
    assert d.max_budget is None and d.max_clip_seconds is None


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


def test_gate_allows_freigabe_mit_hinweisen(tmp_path):
    day = _day(tmp_path, "🟡 FREIGABE MIT HINWEISEN", "✅ OK")
    g = gate_status(day, "youtube")
    assert g["allowed"] is True  # postbar, blockiert nicht
    assert g["tier"] == "hinweise" and "Hinweisen" in g["reason"]


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
