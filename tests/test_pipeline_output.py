"""End-to-End: volle Pipeline mit Stub-LLM + Output-Writer-Struktur."""

from __future__ import annotations

import json

from agency.agents import (
    CommunityManager, ContentStrategist, Copywriter, CreativeDirector, Editor,
    GrowthAnalyst, PostProduction, Publisher, SeoHashtag, TrendScout,
    VideoProducer, VideoScriptwriter, VisualDesigner,
)
from agency.output_writer import write_package
from agency.pipeline import Pipeline


def _full_pipeline(llm):
    return Pipeline([
        TrendScout(llm), ContentStrategist(llm), Copywriter(llm), VideoScriptwriter(llm),
        PostProduction(llm), VisualDesigner(llm), SeoHashtag(llm), CommunityManager(llm),
        VideoProducer(), Editor(llm), Publisher(llm), GrowthAnalyst(llm), CreativeDirector(llm),
    ])


def test_full_run_model_routing_and_websearch(ctx, fake_llm):
    _full_pipeline(fake_llm).run(ctx)
    models = {c["model"] for c in fake_llm.calls}
    assert "claude-opus-4-8" in models  # Creative Director
    assert "claude-sonnet-5" in models  # Fachagents
    assert any(c["web_search"] for c in fake_llm.calls)  # Trend-Scout


def test_full_run_writes_expected_structure(ctx, fake_llm, tmp_output):
    _full_pipeline(fake_llm).run(ctx)
    day = write_package(ctx)

    for pk in ("x", "instagram", "facebook", "youtube"):
        d = day / pk
        for f in ("post.md", "video_script.md", "post_production.md",
                  "visual_prompts.md", "meta.json"):
            assert (d / f).exists(), f"fehlt: {pk}/{f}"

    for f in ("trends.md", "strategy.md", "community.md", "growth.md",
              "director_review.md", "review.md"):
        assert (day / f).exists(), f"Lauf-Datei fehlt: {f}"


def test_meta_json_enriched_by_seo(ctx, fake_llm, tmp_output):
    _full_pipeline(fake_llm).run(ctx)
    day = write_package(ctx)
    meta = json.loads((day / "x" / "meta.json").read_text(encoding="utf-8"))
    assert meta["titel"] == "X (Twitter)-Titel"
    assert meta["hashtags"] and "#auswandern" in meta["hashtags"]
    assert meta["keywords"] and "auswandern" in meta["keywords"]
    assert meta["video_modus"] == "dry_run"


def test_post_md_is_publisher_output_split(ctx, fake_llm, tmp_output):
    _full_pipeline(fake_llm).run(ctx)
    day = write_package(ctx)
    xpost = (day / "x" / "post.md").read_text(encoding="utf-8")
    assert "Finaler X (Twitter)-Post" in xpost
    assert "Instagram-Post" not in xpost  # sauberer Split, kein Leak


def test_review_contains_director_and_costs(ctx, fake_llm, tmp_output):
    _full_pipeline(fake_llm).run(ctx)
    day = write_package(ctx)
    review = (day / "review.md").read_text(encoding="utf-8")
    assert "FREIGABE" in review
    assert "Kosten" in review
    assert ctx.total_cost_usd > 0


def test_pipeline_survives_failing_step(ctx, fake_llm, tmp_output):
    class Boom:
        key, name = "boom", "Boom"

        def run(self, ctx):
            raise RuntimeError("kaputt")

    # Fehlerhafter Schritt darf den Lauf nicht abbrechen.
    Pipeline([Boom(), Copywriter(fake_llm)]).run(ctx)
    assert ctx.get("copywriter")  # nachfolgender Schritt lief trotzdem
