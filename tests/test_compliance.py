"""Compliance-Schicht: Config, Regel-Injektion in Agents, Disclaimer-Anhang."""

from __future__ import annotations

from agency.agents import Copywriter
from agency.config import ROOT, load_config
from agency.context import RunContext
from agency.output_writer import write_package

CRYPTO_CFG = ROOT / "brand_config.crypto.yaml"


def _crypto_ctx():
    cfg = load_config(CRYPTO_CFG)
    return RunContext(config=cfg, pillar=cfg.content_pillars[0], platform="instagram",
                      count=1, topic="Bitcoin Selbstverwahrung", websearch=False)


def test_crypto_config_compliance_enabled():
    cfg = load_config(CRYPTO_CFG)
    assert cfg.compliance_enabled is True
    assert "Keine Anlageberatung" in cfg.disclaimer
    assert len(cfg.compliance_rules) >= 5


def test_default_config_has_no_compliance(cfg):
    assert cfg.compliance_enabled is False
    assert cfg.compliance_block() == ""
    assert cfg.disclaimer == ""


def test_compliance_block_contains_rules():
    cfg = load_config(CRYPTO_CFG)
    block = cfg.compliance_block()
    assert "RECHTLICHE LEITPLANKEN" in block
    assert "Kauf-/Verkaufsempfehlungen" in block
    assert "Disclaimer" in block


def test_agents_receive_compliance_rules(fake_llm):
    ctx = _crypto_ctx()
    bc = Copywriter(fake_llm).brand_context(ctx)
    assert "RECHTLICHE LEITPLANKEN" in bc
    assert "Kauf-/Verkaufsempfehlungen" in bc


def test_disclaimer_appended_to_post(tmp_path, monkeypatch, fake_llm):
    import agency.output_writer as ow
    monkeypatch.setattr(ow, "OUTPUT_ROOT", tmp_path)

    ctx = _crypto_ctx()
    ctx.set("publisher", "## Instagram\n### Post 1\nBitcoin ist spannend. #Bitcoin")
    day = write_package(ctx)

    post = (day / "instagram" / "post.md").read_text(encoding="utf-8")
    assert "Bitcoin ist spannend" in post
    assert "Keine Anlageberatung" in post  # Disclaimer automatisch angehängt


def test_disclaimer_not_duplicated(tmp_path, monkeypatch):
    import agency.output_writer as ow
    monkeypatch.setattr(ow, "OUTPUT_ROOT", tmp_path)

    ctx = _crypto_ctx()
    disc = ctx.config.disclaimer
    ctx.set("publisher", f"## Instagram\n### Post 1\nText.\n\n{disc}")
    day = write_package(ctx)
    post = (day / "instagram" / "post.md").read_text(encoding="utf-8")
    assert post.count("Keine Anlageberatung") == 1  # nicht doppelt
