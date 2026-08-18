"""Gemeinsame Pipeline-Fabrik – von run.py und auto.py genutzt."""

from __future__ import annotations

from .agents import (
    CommunityManager,
    ComplianceOfficer,
    ContentStrategist,
    Copywriter,
    CreativeDirector,
    Editor,
    GrowthAnalyst,
    PostProduction,
    Publisher,
    SeoHashtag,
    TrendScout,
    VideoProducer,
    VideoScriptwriter,
    VisualDesigner,
)
from .llm import LLM
from .pipeline import Pipeline


def build_pipeline(llm: LLM, parallel: bool = False) -> Pipeline:
    """Volle Agentur-Pipeline in Workflow-Reihenfolge (transparent, debugbar).

    Trend-Scout → Stratege → Copywriter/Scriptwriter/Post-Production/Visual/SEO →
    Community → Video-Producer → Lektor → Publisher → Compliance-Prüfer →
    Growth → Creative Director.
    """
    steps = [
        TrendScout(llm),
        ContentStrategist(llm),
        Copywriter(llm),
        VideoScriptwriter(llm),
        PostProduction(llm),
        VisualDesigner(llm),
        SeoHashtag(llm),
        CommunityManager(llm),
        VideoProducer(),          # kein LLM – erzeugt/plant Clips aus Visual-Prompts
        Editor(llm),              # Lektor korrigiert die Post-Texte
        Publisher(llm),           # finale, postbare Fassung -> post.md
        ComplianceOfficer(llm),   # nur im Compliance-Modus: prüft auf rechtliche Risiken
        GrowthAnalyst(llm),
        CreativeDirector(llm),    # Opus – finale Freigabe
    ]
    return Pipeline(steps, parallel=parallel)
