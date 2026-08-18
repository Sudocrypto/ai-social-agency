"""Post-Planung: Zeit-Parsing, Store-Roundtrip, Validierung – offline."""

from __future__ import annotations

import pytest

from agency.scheduling import add_entry, load_schedule, parse_when, remove_entry


def test_parse_when_formats():
    assert parse_when("2026-07-20 09:00") == "2026-07-20T09:00"
    assert parse_when("2026-07-20T09:00") == "2026-07-20T09:00"
    assert parse_when("2026-07-20") == "2026-07-20T00:00"


def test_parse_when_invalid():
    with pytest.raises(ValueError):
        parse_when("morgen früh")


def test_add_and_load(tmp_path):
    store = tmp_path / "schedule.json"
    add_entry("2026-07-20", "youtube", "2026-07-20 09:00", note="ETF", store=store)
    add_entry("2026-07-19", "instagram", "2026-07-19 18:00", store=store)
    entries = load_schedule(store)
    # nach Zeit sortiert -> Instagram (19.) zuerst
    assert entries[0]["platform"] == "instagram"
    assert entries[1]["note"] == "ETF"


def test_add_invalid_platform(tmp_path):
    with pytest.raises(ValueError):
        add_entry("2026-07-20", "tiktok", "2026-07-20 09:00", store=tmp_path / "s.json")


def test_remove_entry(tmp_path):
    store = tmp_path / "s.json"
    add_entry("2026-07-20", "youtube", "2026-07-20 09:00", store=store)
    assert remove_entry(0, store) is True
    assert load_schedule(store) == []
    assert remove_entry(5, store) is False  # Index out of range
