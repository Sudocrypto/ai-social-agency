"""Voiceover: Engine-Auswahl, Kommando-/Argumentbau, Assembly-Anbindung – offline."""

from __future__ import annotations

import pytest

import assemble
from agency.assembly import voiceover


def test_build_say_command():
    cmd = voiceover.build_say_command("Hallo Welt", "/tmp/v.aiff", voice="Anna")
    assert cmd[0] == "say" and "-v" in cmd and "Anna" in cmd
    assert cmd[-1] == "Hallo Welt" and "/tmp/v.aiff" in cmd


def test_build_fal_arguments():
    assert voiceover.build_fal_arguments("Text") == {"text": "Text"}
    a = voiceover.build_fal_arguments("Text", voice="Rachel")
    assert a["voice"] == "Rachel"


def test_synthesize_rejects_empty_text():
    with pytest.raises(ValueError):
        voiceover.synthesize("   ", "/tmp/x.aiff")


def test_synthesize_unknown_engine():
    with pytest.raises(ValueError):
        voiceover.synthesize("Hallo", "/tmp/x.aiff", engine="roboter")


def test_synthesize_fal_needs_key():
    with pytest.raises(RuntimeError):
        voiceover.synthesize("Hallo", "/tmp/x.mp3", engine="fal", api_key=None)


def test_synthesize_say_dispatch(monkeypatch, tmp_path):
    calls = {}

    def fake_say(text, out_path, *, voice="Anna"):
        calls["text"] = text
        calls["voice"] = voice
        return out_path

    monkeypatch.setattr(voiceover, "synthesize_say", fake_say)
    voiceover.synthesize("Hallo", tmp_path / "v.aiff", engine="say", voice="Markus")
    assert calls == {"text": "Hallo", "voice": "Markus"}


def test_assemble_voice_sets_audio_track(tmp_path, monkeypatch, capsys):
    day = tmp_path / "2026-07-19"
    broll = day / "youtube" / "broll"
    broll.mkdir(parents=True)
    (broll / "clip_01.mp4").write_bytes(b"x")
    (day / "youtube" / "post_production.md").write_text(
        "**Untertitel-Text:**\nSatz eins.\n", encoding="utf-8"
    )
    monkeypatch.setattr(assemble, "OUTPUT_ROOT", tmp_path)

    # Stimme nicht wirklich erzeugen (kein macOS `say` im Test) – Datei faken.
    def fake_synth(text, out_path, *, engine="say", voice=None, api_key=None):
        Path = out_path.__class__
        out_path.write_bytes(b"AIFF")
        return out_path

    monkeypatch.setattr(assemble, "synthesize", fake_synth)

    rc = assemble.main([
        "--platform", "youtube", "--date", "2026-07-19", "--auto",
        "--voice", "hallo mein name ist sudo",
    ])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Stimme erzeugt" in out and "Dry-Run" in out
