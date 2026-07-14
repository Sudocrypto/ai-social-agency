"""Video-Producer: Prompt-Parsing, Clip-Längen-Cap und Kosten-Cap (Dry-Run)."""

from __future__ import annotations

from agency.agents import VideoProducer
from agency.video import fal_client


def _visual_md(clips_per_platform: int, seconds: int = 8) -> str:
    lines = []
    for name in ("X (Twitter)", "Instagram", "Facebook", "YouTube"):
        lines.append(f"## {name}")
        for i in range(clips_per_platform):
            lines.append(f"- VIDEO-PROMPT [{seconds}s]: shot {i} for {name}")
    return "\n".join(lines)


def test_dry_run_plans_but_does_not_render(ctx):
    ctx.set("visual_designer", _visual_md(1))
    ctx.config.video["max_video_budget_eur"] = 100.0  # Cap außer Kraft
    out = VideoProducer().run(ctx)
    assert out["mode"] == "dry_run"
    clips = [c for pl in out["per_platform"].values() for c in pl["clips"]]
    assert len(clips) == 4
    assert all(not c["rendered"] and not c.get("skipped") for c in clips)
    assert ctx.video_log and all(e["gerendert"] is False for e in ctx.video_log)


def test_cost_cap_skips_excess_clips(ctx):
    # veo-3.1: 0.40 €/s * 8s = 3.20 € pro Clip; Cap 5 € -> nur 1 Clip passt.
    ctx.set("visual_designer", _visual_md(1))
    ctx.config.video["video_modell"] = "veo-3.1"
    ctx.config.video["max_video_budget_eur"] = 5.0
    out = VideoProducer().run(ctx)
    clips = [c for pl in out["per_platform"].values() for c in pl["clips"]]
    planned = [c for c in clips if not c.get("skipped")]
    skipped = [c for c in clips if c.get("skipped")]
    assert len(planned) == 1 and len(skipped) == 3
    assert ctx.total_video_cost_eur <= 5.0


def test_clip_length_capped_to_max(ctx):
    ctx.set("visual_designer", "## X (Twitter)\n- VIDEO-PROMPT [30s]: long shot")
    ctx.config.video["max_clip_sekunden"] = 8
    ctx.config.video["max_video_budget_eur"] = 100.0
    out = VideoProducer().run(ctx)
    clip = out["per_platform"]["x"]["clips"][0]
    assert clip["seconds"] == 8  # von 30 auf 8 gekappt


def test_no_prompts_no_clips(ctx):
    ctx.set("visual_designer", "## X (Twitter)\nnur Text, kein VIDEO-PROMPT")
    out = VideoProducer().run(ctx)
    assert all(pl["clips"] == [] for pl in out["per_platform"].values())
    assert ctx.total_video_cost_eur == 0.0


def test_cost_estimate_matches_price_table():
    assert fal_client.estimate_cost_eur("veo-3.1", 8) == round(0.40 * 8, 4)
    assert fal_client.estimate_cost_eur("seedance-2.0-fast", 5) == round(0.08 * 5, 4)
