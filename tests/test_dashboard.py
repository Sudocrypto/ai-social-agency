"""Dashboard: Post-Log, Zustandssammlung, HTML-Rendering – offline."""

from __future__ import annotations

from agency.dashboard.html import render_html
from agency.dashboard.state import gather_state
from agency.publishing.post_log import load_post_log, record_post


def test_post_log_roundtrip(tmp_path):
    store = tmp_path / "post_log.json"
    record_post("x", "https://x.com/1", "2026-07-15", store=store)
    record_post("facebook", None, "2026-07-15", store=store)
    log = load_post_log(store)
    assert len(log) == 2
    assert log[0]["platform"] == "x" and log[0]["url"] == "https://x.com/1"
    assert log[1]["url"] == ""  # None -> ""


def _pkg(day, platform, director_status):
    p = day / platform
    p.mkdir(parents=True)
    (p / "post.md").write_text(f"## {platform}\n### Post 1\nText.", encoding="utf-8")
    (day / "director_review.md").write_text(
        f"# Freigabe\n### {platform}\n**Status:** {director_status}\n", encoding="utf-8"
    )


def test_gather_state_statuses(tmp_path):
    out = tmp_path / "output"
    day = out / "2026-07-15"
    _pkg(day, "instagram", "✅ FREIGABE")
    # youtube blockiert (NACHBESSERN) – zweite Plattform am selben Tag
    yp = day / "youtube"
    yp.mkdir()
    (yp / "post.md").write_text("## youtube\n### Post 1\nText.", encoding="utf-8")
    (day / "director_review.md").write_text(
        "# Freigabe\n### Instagram\n**Status:** ✅ FREIGABE\n"
        "### YouTube\n**Status:** ⚠️ NACHBESSERN\n", encoding="utf-8"
    )

    store = tmp_path / "post_log.json"
    record_post("x", "https://x/1", "2026-07-14", store=store)
    day2 = out / "2026-07-14"
    _pkg(day2, "x", "✅ FREIGABE")

    state = gather_state(out, post_log_store=store, metrics_csv=tmp_path / "none.csv")

    # Neueste zuerst
    assert state["packages"][0]["date"] == "2026-07-15"
    statuses = {
        (pkg["date"], p["platform"]): p["status"]
        for pkg in state["packages"] for p in pkg["platforms"]
    }
    assert statuses[("2026-07-15", "instagram")] == "bereit"
    assert statuses[("2026-07-15", "youtube")] == "blockiert"
    assert statuses[("2026-07-14", "x")] == "gepostet"
    assert state["counts"]["gepostet"] == 1
    assert state["counts"]["geplant"] == 1  # nur instagram ist bereit


def test_gather_state_performance(tmp_path):
    out = tmp_path / "output"
    out.mkdir()
    csv = tmp_path / "metrics.csv"
    csv.write_text(
        "plattform,titel,views,likes,comments,engagement_pct\n"
        "youtube,News A,1000,50,10,6.0\nyoutube,News B,5000,200,30,4.6\n",
        encoding="utf-8",
    )
    state = gather_state(out, post_log_store=tmp_path / "pl.json", metrics_csv=csv)
    perf = state["performance"]
    assert perf[0]["titel"] == "News B"  # nach Views sortiert
    assert perf[0]["views"] == 5000


def test_render_html_contains_sections(tmp_path):
    out = tmp_path / "output"
    day = out / "2026-07-15"
    _pkg(day, "instagram", "✅ FREIGABE")
    state = gather_state(out, post_log_store=tmp_path / "pl.json",
                         metrics_csv=tmp_path / "n.csv")
    html = render_html(state)
    assert "<!doctype html>" in html
    assert "Dashboard" in html
    assert "2026-07-15" in html and "Instagram" in html
    assert "Als Nächstes geplant" in html and "Entwürfe" in html and "Gepostet" in html


def test_gather_state_schedule_statuses(tmp_path):
    import json

    out = tmp_path / "output"
    out.mkdir()
    sched = tmp_path / "schedule.json"
    sched.write_text(json.dumps([
        {"package_date": "2026-01-01", "platform": "youtube", "at": "2020-01-01T09:00", "note": "alt"},
        {"package_date": "2099-01-01", "platform": "instagram", "at": "2099-01-01T09:00", "note": ""},
        {"package_date": "2026-07-14", "platform": "x", "at": "2099-01-01T10:00", "note": ""},
    ]), encoding="utf-8")
    store = tmp_path / "pl.json"
    record_post("x", "https://x/1", "2026-07-14", store=store)

    state = gather_state(out, post_log_store=store, schedule_store=sched,
                         metrics_csv=tmp_path / "n.csv")
    by = {(s["platform"]): s["status"] for s in state["scheduled"]}
    assert by["youtube"] == "überfällig"     # Termin in der Vergangenheit
    assert by["instagram"] == "geplant"      # Termin in der Zukunft
    assert by["x"] == "gepostet"             # bereits im Post-Log
    assert state["counts"]["termine"] == 2   # gepostete zählen nicht mehr

    html = render_html(state)
    assert "Als Nächstes geplant" in html and "Überfällig" in html


def test_render_html_empty_state():
    state = {"generated_at": "2026-07-15T10:00:00", "packages": [], "posts": [],
             "performance": [], "counts": {"pakete": 0, "geplant": 0, "gepostet": 0}}
    html = render_html(state)
    assert "Noch keine Pakete" in html and "Noch nichts gepostet" in html
