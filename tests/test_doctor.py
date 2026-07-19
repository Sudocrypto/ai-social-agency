"""Preflight-Check: Einzelprüfungen + Gesamtstatus – offline."""

from __future__ import annotations

from agency.config import ROOT, load_config
from agency.doctor import (
    FAIL,
    OK,
    WARN,
    check_anthropic_key,
    check_budget,
    check_fal_client,
    check_fal_key,
    check_ffmpeg,
    check_python,
    check_video_model,
    run_checks,
    worst_status,
)


def test_python_ok():
    assert check_python((3, 11)).status == OK
    assert check_python((3, 12)).status == OK


def test_python_too_old_fails():
    assert check_python((3, 9)).status == FAIL


def test_anthropic_key_missing_fails():
    c = check_anthropic_key(None)
    assert c.status == FAIL and "fehlt" in c.detail


def test_anthropic_key_placeholder_fails():
    assert check_anthropic_key("sk-ant-").status == FAIL  # zu kurz


def test_anthropic_key_valid_ok():
    assert check_anthropic_key("sk-ant-" + "x" * 50).status == OK


def test_fal_key_missing_warns_when_video():
    assert check_fal_key(None, needs_video=True).status == WARN


def test_fal_key_missing_ok_when_no_video():
    assert check_fal_key(None, needs_video=False).status == OK


def test_fal_key_valid_ok():
    assert check_fal_key("abcd1234-ef56:deadbeefcafe0000", needs_video=True).status == OK


def test_fal_key_without_colon_warns():
    assert check_fal_key("keinDoppelpunktHierDrin1234", needs_video=True).status == WARN


def test_fal_client_and_ffmpeg_injectable():
    assert check_fal_client(importable=True).status == OK
    assert check_fal_client(importable=False).status == WARN
    assert check_ffmpeg(available=True).status == OK
    assert check_ffmpeg(available=False).status == WARN


def test_video_model_known_and_unknown():
    cfg = load_config(ROOT / "brand_config.ki.yaml")
    assert check_video_model(cfg).status == OK  # seedance-2.0-fast ist bekannt
    cfg.video["video_modell"] = "gibt-es-nicht"
    assert check_video_model(cfg).status == FAIL


def test_budget_reports_clip_count():
    cfg = load_config(ROOT / "brand_config.ki.yaml")
    cfg.video["max_video_budget_eur"] = 1.0  # unter 1 Clip-Preis
    assert check_budget(cfg).status == WARN
    cfg.video["max_video_budget_eur"] = 20.0
    assert check_budget(cfg).status == OK  # reicht für >=3 Clips


def test_run_checks_and_worst_status():
    cfg = load_config(ROOT / "brand_config.ki.yaml")
    checks = run_checks(cfg, needs_video=True)
    names = {c.name for c in checks}
    assert "ANTHROPIC_API_KEY" in names and "ffmpeg" in names and "Video-Budget" in names
    # Gesamtstatus ist der schlechteste Einzelstatus.
    assert worst_status(checks) in (OK, WARN, FAIL)
    assert worst_status([]) == OK
