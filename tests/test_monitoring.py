"""Monitoring: ID-Parsing, Tracker, Engagement/Report, CSV-Export – offline."""

from __future__ import annotations

import pytest

from agency.metrics import Metrics
from agency.monitoring.report import build_report, engagement_rate, rank, to_metrics_csv
from agency.monitoring.tracker import Tracker, parse_video_id

STATS = [
    {"video_id": "aaaaaaaaaaa", "titel": "News A", "views": 1000, "likes": 100, "comments": 20},
    {"video_id": "bbbbbbbbbbb", "titel": "News B", "views": 5000, "likes": 150, "comments": 30},
    {"video_id": "ccccccccccc", "titel": "News C", "views": 0, "likes": 0, "comments": 0},
]


@pytest.mark.parametrize("inp,expected", [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
])
def test_parse_video_id(inp, expected):
    assert parse_video_id(inp) == expected


def test_parse_video_id_invalid():
    with pytest.raises(ValueError):
        parse_video_id("kein-video")


def test_tracker_roundtrip(tmp_path):
    store = tmp_path / "tracking.json"
    t = Tracker(store)
    t.add("https://youtu.be/dQw4w9WgXcQ", thema="Bitcoin ETF")
    assert t.video_ids() == ["dQw4w9WgXcQ"]
    # Neu laden -> persistiert
    t2 = Tracker(store)
    assert t2.items[0].thema == "Bitcoin ETF"


def test_tracker_rejects_duplicate(tmp_path):
    t = Tracker(tmp_path / "t.json")
    t.add("dQw4w9WgXcQ")
    with pytest.raises(ValueError):
        t.add("https://youtu.be/dQw4w9WgXcQ")


def test_engagement_rate():
    assert engagement_rate({"views": 1000, "likes": 100, "comments": 20}) == 12.0
    assert engagement_rate({"views": 0, "likes": 5, "comments": 5}) == 0.0  # keine Division


def test_rank_sorts_by_views():
    r = rank(STATS)
    assert [s["video_id"] for s in r] == ["bbbbbbbbbbb", "aaaaaaaaaaa", "ccccccccccc"]
    assert r[0]["engagement_pct"] == round(180 / 5000 * 100, 2)


def test_build_report_contains_ranking():
    md = build_report(STATS)
    assert "Ranking" in md and "News B" in md
    assert "Bestes Engagement" in md


def test_build_report_empty():
    assert "Keine Daten" in build_report([])


def test_metrics_csv_plugs_into_growth_analyst(tmp_path):
    csv_text = to_metrics_csv(STATS)
    f = tmp_path / "metrics.csv"
    f.write_text(csv_text, encoding="utf-8")
    # Der Growth-Analyst-Loader muss das Format verstehen.
    m = Metrics.load(f)
    agg = m.aggregates()
    assert agg["youtube"]["views"] == 6000  # 1000 + 5000 + 0


def test_anon_brand_hashtag():
    from agency.config import ROOT, load_config
    cfg = load_config(ROOT / "brand_config.crypto.yaml")
    assert cfg.brand_name == "Anon Bitcoin News"
    assert cfg.branded_hashtag == "#AnonBitcoinNews"
    assert cfg.compliance_enabled is True
