"""Performance-Daten-Import (CSV/JSON) + datengetriebener Growth-Analyst."""

from __future__ import annotations

import json

import pytest

from agency.agents import GrowthAnalyst
from agency.metrics import Metrics


def test_load_csv_and_aggregate(tmp_path):
    f = tmp_path / "m.csv"
    f.write_text(
        "plattform,impressions,likes\nx,1000,50\nx,500,20\ninstagram,2000,300\n",
        encoding="utf-8",
    )
    m = Metrics.load(f)
    assert len(m.rows) == 3
    agg = m.aggregates()
    assert agg["x"]["impressions"] == 1500 and agg["x"]["likes"] == 70
    assert agg["instagram"]["impressions"] == 2000


def test_to_markdown_has_table_and_sums(tmp_path):
    f = tmp_path / "m.csv"
    f.write_text("plattform,impressions\nx,1000\ninstagram,2000\n", encoding="utf-8")
    md = Metrics.load(f).to_markdown()
    assert "| plattform | impressions |" in md
    assert "Summen pro Plattform" in md
    assert "x: impressions=1000" in md


def test_load_json_dict_of_dicts(tmp_path):
    f = tmp_path / "m.json"
    f.write_text(json.dumps({"x": {"likes": 10}, "youtube": {"likes": 99}}), encoding="utf-8")
    m = Metrics.load(f)
    assert {r["plattform"] for r in m.rows} == {"x", "youtube"}
    assert m.aggregates()["youtube"]["likes"] == 99


def test_load_json_list(tmp_path):
    f = tmp_path / "m.json"
    f.write_text(json.dumps([{"plattform": "x", "saves": 5}]), encoding="utf-8")
    assert Metrics.load(f).rows == [{"plattform": "x", "saves": 5}]


def test_load_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        Metrics.load(tmp_path / "nope.csv")
    bad = tmp_path / "m.txt"
    bad.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        Metrics.load(bad)
    empty = tmp_path / "e.csv"
    empty.write_text("plattform,likes\n", encoding="utf-8")
    with pytest.raises(ValueError):
        Metrics.load(empty)


def test_non_numeric_ignored_in_aggregates(tmp_path):
    f = tmp_path / "m.csv"
    f.write_text("plattform,note,likes\nx,gut,10\n", encoding="utf-8")
    agg = Metrics.load(f).aggregates()
    assert "note" not in agg["x"] and agg["x"]["likes"] == 10


def test_growth_analyst_prompt_uses_metrics(ctx):
    ctx.metrics = "| plattform | likes |\n|---|---|\n| x | 42 |\n\n**Summen pro Plattform:**\n- x: likes=42"
    prompt = GrowthAnalyst(None).build_prompt(ctx)
    assert "GELIEFERTE PERFORMANCE-DATEN" in prompt
    assert "likes=42" in prompt
    assert "Daten-Analyse" in prompt


def test_growth_analyst_prompt_baseline_without_metrics(ctx):
    ctx.metrics = None
    prompt = GrowthAnalyst(None).build_prompt(ctx)
    assert "keine Daten geliefert" in prompt
    assert "KPIs pro Plattform" in prompt
