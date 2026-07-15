"""Freigabe-Gate: Director-Urteil parsen + im publish-Flow durchsetzen."""

from __future__ import annotations

import json

import publish
from agency.publishing.approval import load_approvals, parse_approvals

DIRECTOR_MD = """# Creative-Director-Freigabe

## Freigabe pro Plattform
### X (Twitter)
**Status:** ✅ FREIGABE
**Begründung:** Starker Hook.

### Instagram
**Status:** ⚠️ NACHBESSERN
**Begründung:** Caption zu lang.

### Facebook
**Status:** ✅ FREIGABE

### YouTube
**Status:** ⚠️ NACHBESSERN
"""


def test_parse_approvals():
    a = parse_approvals(DIRECTOR_MD)
    assert a["x"]["approved"] is True
    assert a["facebook"]["approved"] is True
    assert a["instagram"]["approved"] is False
    assert a["youtube"]["approved"] is False


def test_parse_approvals_missing_platform_is_unknown():
    a = parse_approvals("# Freigabe\n### X (Twitter)\n**Status:** ✅ FREIGABE")
    assert a["x"]["approved"] is True
    assert a["instagram"]["approved"] is None  # kein Urteil


def test_load_approvals(tmp_path):
    (tmp_path / "director_review.md").write_text(DIRECTOR_MD, encoding="utf-8")
    a = load_approvals(tmp_path)
    assert a["instagram"]["approved"] is False


def _make_package(day_dir):
    for pk in ("x", "instagram", "facebook", "youtube"):
        p = day_dir / pk
        p.mkdir(parents=True)
        (p / "post.md").write_text(f"## {pk}\n### Post 1\nText für {pk}. #tag", encoding="utf-8")
        (p / "meta.json").write_text(json.dumps({"titel": "T"}), encoding="utf-8")
    (day_dir / "director_review.md").write_text(DIRECTOR_MD, encoding="utf-8")


def test_publish_skips_nachbessern(tmp_path, monkeypatch, capsys):
    day = tmp_path / "2026-07-14"
    _make_package(day)
    monkeypatch.setattr(publish, "OUTPUT_ROOT", tmp_path)

    rc = publish.main(["--date", "2026-07-14", "--platform", "all"])  # Dry-Run
    out = capsys.readouterr().out
    assert rc == 0
    # Instagram + YouTube (NACHBESSERN) übersprungen, X + Facebook nicht.
    assert "Instagram: ⛔" in out and "YouTube: ⛔" in out
    assert "X (Twitter): ⛔" not in out
    assert "WÜRDE auf X (Twitter) posten" in out


def test_publish_force_overrides(tmp_path, monkeypatch, capsys):
    day = tmp_path / "2026-07-14"
    _make_package(day)
    monkeypatch.setattr(publish, "OUTPUT_ROOT", tmp_path)

    publish.main(["--date", "2026-07-14", "--platform", "instagram", "--force"])
    out = capsys.readouterr().out
    assert "Instagram: ⛔" not in out  # trotz NACHBESSERN nicht mehr geblockt
