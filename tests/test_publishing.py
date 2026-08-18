"""Publishing-Schicht: Validierung, Credential-Preflight, Dry-Run, Loader – offline."""

from __future__ import annotations

from pathlib import Path

import pytest

from agency.publishing import Post, get_publisher
from agency.publishing.credentials import ALL_ENV_KEYS, platform_ready
from agency.publishing.loader import extract_variant, load_post
from agency.publishing.registry import PUBLISHERS
from agency.publishing.x_publisher import XPublisher

NO_CREDS: dict[str, str | None] = {k: None for k in ALL_ENV_KEYS}


def test_registry_has_all_platforms():
    assert set(PUBLISHERS) == {"x", "instagram", "facebook", "youtube"}
    assert get_publisher("x").name == "X (Twitter)"


def test_registry_invalid():
    with pytest.raises(ValueError):
        get_publisher("tiktok")


def test_x_thread_split_numbered():
    text = "1/ Erster Teil\n2/ Zweiter Teil\n3/ Dritter Teil"
    tweets = XPublisher._split_thread(text)
    assert len(tweets) == 3 and tweets[0].startswith("1/")


def test_x_validate_long_single_tweet_fails():
    pub = get_publisher("x")
    errors = pub.validate(Post(platform="x", text="x" * 300))
    assert any("zu lang" in e for e in errors)


def test_x_validate_short_ok():
    pub = get_publisher("x")
    assert pub.validate(Post(platform="x", text="Kurz und knackig. #auswandern")) == []


def test_facebook_dry_run_warns_about_missing_creds():
    pub = get_publisher("facebook")
    res = pub.publish(Post(platform="facebook", text="Hallo Welt"), NO_CREDS, dry_run=True)
    assert res.ok and res.dry_run
    assert any("FB_PAGE_ID" in w for w in res.warnings)


def test_live_without_creds_aborts_before_network():
    pub = get_publisher("facebook")
    res = pub.publish(Post(platform="facebook", text="Hallo"), NO_CREDS, dry_run=False)
    assert not res.ok and not res.dry_run
    assert "Fehlende Env" in (res.error or "")


def test_instagram_requires_media_url():
    pub = get_publisher("instagram")
    errors = pub.validate(Post(platform="instagram", text="Caption"))
    assert any("Medien-URL" in e for e in errors)
    ok = pub.validate(Post(platform="instagram", text="Caption",
                           media_urls=["https://x/y.jpg"]))
    assert ok == []


def test_youtube_requires_title_and_video():
    pub = get_publisher("youtube")
    errors = pub.validate(Post(platform="youtube", text="Beschreibung", title=None))
    assert any("Titel" in e for e in errors)
    assert any("Videodatei" in e for e in errors)


def test_youtube_with_video_and_title_ok():
    pub = get_publisher("youtube")
    errors = pub.validate(
        Post(platform="youtube", text="Desc", title="Mein Titel",
             media=[Path("final.mp4")])
    )
    assert errors == []


def test_platform_ready_reports_missing():
    ready, missing = platform_ready("x", NO_CREDS)
    assert not ready and set(missing) == set(get_publisher("x").required_env)


def test_extract_variant_strips_headers():
    md = (
        "## X (Twitter)\n### Post 1\nErster Post-Text. #tag\n\n"
        "### Post 2\nZweiter Post-Text."
    )
    assert extract_variant(md, 1) == "Erster Post-Text. #tag"
    assert extract_variant(md, 2) == "Zweiter Post-Text."


def test_load_post_from_package(tmp_path):
    d = tmp_path / "x"
    d.mkdir()
    (d / "post.md").write_text("## X (Twitter)\n### Post 1\nHallo Welt #x", encoding="utf-8")
    (d / "meta.json").write_text('{"titel": "T", "description": "D"}', encoding="utf-8")
    post = load_post(tmp_path, "x")
    assert post.text == "Hallo Welt #x" and post.title == "T"
