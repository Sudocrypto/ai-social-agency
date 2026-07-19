"""Video-Assembly: Plan-I/O, SRT-Timing, ffmpeg-Kommando, Scaffold – offline."""

from __future__ import annotations

import assemble
from agency.assembly.builder import SRT_NAME, build_command, render
from agency.assembly.plan import AssemblyPlan, Music, Segment
from agency.assembly.scaffold import extract_subtitles, scaffold_plan
from agency.assembly.subtitles import _ts, build_srt


def _plan(**kw) -> AssemblyPlan:
    return AssemblyPlan(
        segments=[
            Segment(source="a.mp4", start=0, end=4, subtitle="Hallo Welt", mute=False),
            Segment(source="b.mp4", start=1, end=3, subtitle="Zweiter Clip", mute=True),
        ],
        music=Music(source="m.mp3", gain_db=-18.0),
        **kw,
    )


def test_segment_duration_and_total():
    p = _plan()
    assert p.segments[0].duration == 4.0
    assert p.segments[1].duration == 2.0
    assert p.total_duration == 6.0


def test_validate_catches_bad_plan():
    empty = AssemblyPlan()
    assert any("Keine Segmente" in e for e in empty.validate())
    bad = AssemblyPlan(segments=[Segment(source="x.mp4", start=5, end=2)])
    assert any("end" in e for e in bad.validate())


def test_plan_roundtrip(tmp_path):
    p = _plan(width=1920, height=1080)
    path = p.save(tmp_path / "assembly.json")
    loaded = AssemblyPlan.load(path)
    assert loaded.to_dict() == p.to_dict()
    assert loaded.music and loaded.music.source == "m.mp3"


def test_srt_timing():
    srt = build_srt(_plan())
    assert "00:00:00,000 --> 00:00:04,000" in srt   # Segment 1 (4s)
    assert "00:00:04,000 --> 00:00:06,000" in srt   # Segment 2 (2s, kumuliert)
    assert "Hallo Welt" in srt and "Zweiter Clip" in srt


def test_ts_format():
    assert _ts(3661.5) == "01:01:01,500"


def test_build_command_structure():
    cmd = build_command(_plan(), "final.mp4")
    assert cmd[0] == "ffmpeg"
    # ein -i pro Segment + eins für Musik
    assert cmd.count("-i") == 3
    assert "-filter_complex" in cmd
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "concat=n=2:v=1:a=1[vc][ac]" in fc
    assert f"subtitles={SRT_NAME}" in fc          # Untertitel eingebrannt
    assert "anullsrc" in fc                       # stummes Segment -> Stille
    assert "amix=inputs=2" in fc                  # Musik untergemischt
    assert "libx264" in cmd and "final.mp4" in cmd


def test_build_command_without_music_or_subs():
    p = AssemblyPlan(segments=[Segment(source="a.mp4", start=0, end=2, mute=True)])
    cmd = build_command(p, "out.mp4")
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "[vc]copy[vout]" in fc     # keine Untertitel
    assert "amix" not in fc           # keine Musik
    assert cmd.count("-i") == 1


def test_render_dry_run_writes_srt_but_no_video(tmp_path):
    out = tmp_path / "final.mp4"
    res = render(_plan(), out, dry_run=True)
    assert res["ok"] and not res["rendered"]
    assert res["cmd"] and "ffmpeg" in res["cmd"]
    assert (tmp_path / SRT_NAME).exists()   # SRT zur Vorschau geschrieben
    assert not out.exists()                 # aber kein Video gerendert


def test_render_invalid_plan():
    res = render(AssemblyPlan(), "x.mp4", dry_run=True)
    assert not res["ok"] and "Keine Segmente" in res["error"]


def test_extract_subtitles_splits_sentences():
    md = "**Cut-Liste:**\n| 1 |\n\n**Untertitel-Text:**\nHallo. Ich bin weg! Und jetzt?\n\n**Musik:**\n- ruhig"
    subs = extract_subtitles(md)
    assert subs == ["Hallo.", "Ich bin weg!", "Und jetzt?"]


def test_scaffold_from_package(tmp_path):
    day = tmp_path / "2026-07-14"
    pdir = day / "youtube"
    (pdir / "broll").mkdir(parents=True)
    (pdir / "post_production.md").write_text(
        "**Untertitel-Text:**\nSatz eins. Satz zwei.\n", encoding="utf-8"
    )
    (pdir / "broll" / "clip_01.mp4").write_bytes(b"x")

    plan = scaffold_plan(day, "youtube")
    assert plan.width == 1920 and plan.height == 1080  # YouTube = Querformat
    sources = [s.source for s in plan.segments]
    assert "EIGENES_MATERIAL.mp4" in sources           # eigener Auftakt-Platzhalter
    assert any(s.endswith("clip_01.mp4") for s in sources)  # generierte B-Roll übernommen
    broll_seg = next(s for s in plan.segments if s.source.endswith("clip_01.mp4"))
    assert broll_seg.mute is True                      # KI-B-Roll stumm
    assert plan.music and plan.music.source == "MUSIK.mp3"


def test_assemble_auto_builds_from_rendered_clips(tmp_path, monkeypatch, capsys):
    # --auto baut aus vorhandenen broll/-Clips ein Video (Dry-Run, keine Render-Kosten).
    day = tmp_path / "2026-07-19"
    broll = day / "youtube" / "broll"
    broll.mkdir(parents=True)
    (broll / "clip_01.mp4").write_bytes(b"x")
    (broll / "clip_02.mp4").write_bytes(b"x")
    (day / "youtube" / "post_production.md").write_text(
        "**Untertitel-Text:**\nSatz eins. Satz zwei.\n", encoding="utf-8"
    )
    monkeypatch.setattr(assemble, "OUTPUT_ROOT", tmp_path)

    rc = assemble.main(["--platform", "youtube", "--date", "2026-07-19", "--auto"])
    out = capsys.readouterr().out
    assert rc == 0 and "Dry-Run" in out  # ohne --render nur Dry-Run


def test_assemble_auto_errors_without_clips(tmp_path, monkeypatch, capsys):
    day = tmp_path / "2026-07-19"
    (day / "youtube").mkdir(parents=True)
    monkeypatch.setattr(assemble, "OUTPUT_ROOT", tmp_path)

    rc = assemble.main(["--platform", "youtube", "--date", "2026-07-19", "--auto"])
    assert rc == 2  # keine gerenderten Clips -> klarer Fehler


def test_srt_name_has_no_leading_dot():
    # Führender Punkt bricht den ffmpeg-subtitles-Filter ("No option name").
    assert not SRT_NAME.startswith(".")


def test_assemble_reuses_existing_voice_without_recharge(tmp_path, monkeypatch, capsys):
    day = tmp_path / "2026-07-19"
    broll = day / "youtube" / "broll"
    broll.mkdir(parents=True)
    (broll / "clip_01.mp4").write_bytes(b"x")
    (day / "youtube" / "voiceover.mp3").write_bytes(b"AUDIO")  # existiert bereits
    monkeypatch.setattr(assemble, "OUTPUT_ROOT", tmp_path)

    def boom(*a, **k):  # darf NICHT aufgerufen werden
        raise AssertionError("synthesize hätte nicht aufgerufen werden dürfen")

    monkeypatch.setattr(assemble, "synthesize", boom)
    rc = assemble.main([
        "--platform", "youtube", "--date", "2026-07-19", "--auto",
        "--voice", "egal", "--voice-engine", "fal",
    ])
    out = capsys.readouterr().out
    assert rc == 0 and "wiederverwendet" in out
