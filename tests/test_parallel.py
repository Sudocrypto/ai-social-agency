"""Abhängigkeitsgraph + parallele Ausführung: Ebenen korrekt, Ergebnis identisch."""

from __future__ import annotations

from agency.agents import (
    CommunityManager, ContentStrategist, Copywriter, CreativeDirector, Editor,
    GrowthAnalyst, PostProduction, Publisher, SeoHashtag, TrendScout,
    VideoProducer, VideoScriptwriter, VisualDesigner,
)
from agency.graph import DEPENDENCIES, compute_levels
from agency.pipeline import Pipeline


def _steps(llm):
    return [
        TrendScout(llm), ContentStrategist(llm), Copywriter(llm), VideoScriptwriter(llm),
        PostProduction(llm), VisualDesigner(llm), SeoHashtag(llm), CommunityManager(llm),
        VideoProducer(), Editor(llm), Publisher(llm), GrowthAnalyst(llm), CreativeDirector(llm),
    ]


def test_levels_respect_dependencies():
    keys = list(DEPENDENCIES.keys())
    levels = compute_levels(keys)
    level_of = {k: i for i, lvl in enumerate(levels) for k in lvl}
    # Jede Abhängigkeit liegt in einer strikt früheren Ebene.
    for key, deps in DEPENDENCIES.items():
        for d in deps:
            assert level_of[d] < level_of[key], f"{d} muss vor {key} liegen"


def test_known_level_structure():
    levels = compute_levels(list(DEPENDENCIES.keys()))
    assert levels[0] and "trend_scout" in levels[0]
    # copywriter und video_scriptwriter sind unabhängig -> gleiche Ebene.
    lvl = {k: i for i, l in enumerate(levels) for k in l}
    assert lvl["copywriter"] == lvl["video_scriptwriter"]
    assert lvl["seo_hashtag"] == lvl["community_manager"] == lvl["editor"]
    assert lvl["creative_director"] == len(levels) - 1  # ganz am Ende


def test_cycle_detected():
    import pytest

    with pytest.raises(ValueError):
        compute_levels(["a", "b"], {"a": ["b"], "b": ["a"]})


def test_missing_dep_ignored():
    # Fehlende (nicht vorhandene) Abhängigkeit blockiert nicht.
    levels = compute_levels(["copywriter"], DEPENDENCIES)
    assert levels == [["copywriter"]]


def test_parallel_matches_sequential(ctx, fake_llm):
    from agency.config import load_config
    from agency.context import RunContext

    Pipeline(_steps(fake_llm), parallel=False).run(ctx)
    seq_keys = set(ctx.outputs.keys())

    cfg2 = load_config()
    ctx2 = RunContext(config=cfg2, pillar=cfg2.content_pillars[0], platform="all",
                      count=1, topic="Erster Monat Thailand", websearch=True)
    from tests.conftest import FakeLLM

    Pipeline(_steps(FakeLLM()), parallel=True).run(ctx2)
    par_keys = set(ctx2.outputs.keys())

    assert seq_keys == par_keys  # dieselben Agents liefen
    assert ctx2.get("publisher") and ctx2.get("creative_director")
    # Publisher hat lektorierte Fassung genutzt (Reihenfolge korrekt eingehalten).
    assert "Finaler" in str(ctx2.get("publisher"))
