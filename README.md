# AI Social Media Agency — "Danilo Takes Off"

Ein Multi-Agent-System in Python, das wie eine komplette Social-Media-Agentur
funktioniert: spezialisierte KI-Agents ("Mitarbeiter") produzieren gemeinsam
fertigen Content für X, Instagram, Facebook und YouTube – inkl. Briefings für
KI-Video-Clips. **Phase 1:** Content wird generiert und zur Freigabe exportiert
(kein automatisches Posten).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # dann ANTHROPIC_API_KEY eintragen (FAL_KEY optional)
```

`.env` wird nie committet. Keys stehen ausschließlich dort, nie im Code.

## Nutzung

```bash
python run.py --pillar auswandern --platform all --count 5
python run.py --pillar reise --platform instagram --topic "Erster Monat Thailand"
python run.py --pillar auswandern --no-websearch     # kostenloser Testlauf (keine Websuche)
python run.py --pillar auswandern --render-video      # echte fal.ai-Clips (Phase 3)
```

| Flag | Bedeutung |
|---|---|
| `--pillar` | Content-Pillar (Kurzform wie `auswandern`) oder freies Thema |
| `--platform` | `x` / `instagram` / `facebook` / `youtube` / `all` (Standard) |
| `--count` | Post-Varianten pro Plattform |
| `--topic` | konkretes Thema (überschreibt die Pillar-Ableitung) |
| `--no-websearch` | Live-Websuche des Trend-Scouts aus |
| `--render-video` | echtes Video-Rendering statt Dry-Run (braucht `FAL_KEY`) |
| `--parallel` | unabhängige Agents parallel ausführen (schneller); Default sequenziell/debugbar |

Konfiguration (Marke, Modelle, Video-Modus, Kosten-Cap): **`brand_config.yaml`**.

## Die Agents

Creative Director (Opus, Freigabe) · Trend-Scout (Web-Search) · Content-Stratege ·
Copywriter · Video-Scriptwriter · Post-Production-Briefing · Visual Designer ·
Video-Producer (fal.ai, Dry-Run + Kosten-Cap) · SEO/Hashtag · Community Manager ·
Lektor/Editor · Growth-Analyst · Publisher/Platform-Adapter.

Der Creative Director läuft auf **Opus**, alle Fachagents auf **Sonnet**
(pro Agent überschreibbar via `model_overrides` in `brand_config.yaml`).

## Ausgabe

```
output/{datum}/
  {plattform}/
    post.md              finaler, postbarer Text + Hashtags
    video_script.md      Skript + Shotlist (falls relevant)
    post_production.md   Schnittplan (Cut-Liste, B-Roll, Untertitel, Musik)
    visual_prompts.md    Bild-/Video-Prompts + Thumbnail-Idee
    broll/               .mp4-Clips (Render) bzw. Plan + Prompts (Dry-Run)
    meta.json            Titel, Description, Keywords, Hashtags, Video-Kosten
  trends.md · strategy.md · community.md · growth.md · director_review.md
  review.md              konsolidierte Übersicht zur Freigabe
```

## Video-Producer & Kosten

Standard ist **Dry-Run**: Prompts werden geplant und Kosten geschätzt, es wird
nichts gerendert. Erst `--render-video` (mit gültigem `FAL_KEY`) ruft die
fal.ai-API. In beiden Fällen gilt `max_video_budget_eur` pro Durchlauf als Cap –
darüber hinausgehende Clips werden übersprungen und im Plan vermerkt. Modell
wählbar via `video_modell` (`veo-3.1` / `seedance-2.0-fast` / `kling-3.0`),
Clip-Länge via `max_clip_sekunden`.

## Tests

Offline-Regressionssuite (gestubbtes LLM, kein API-Key nötig):

```bash
pip install -r requirements-dev.txt
pytest
```

Deckt ab: Modell-Routing (Opus/Sonnet), Plattform-Split, SEO-Parsing in
`meta.json`, Video-Prompt-Parsing + Kosten-Cap und die komplette
Output-Struktur.

## Architektur

Transparente Pipeline (`agency/pipeline.py`) – kein Blackbox-Framework. Jeder
Agent ist ein eigenes Modul unter `agency/agents/` mit eigenem System-Prompt und
klarer Rolle. Der `RunContext` (`agency/context.py`) trägt alle Zwischenergebnisse
und das Kosten-Log durch die Pipeline. Standard ist sequenzielle Ausführung
(maximal debugbar); mit `--parallel` laufen unabhängige Agents je Abhängigkeits-
Ebene (`agency/graph.py`) gleichzeitig – Ergebnis identisch. CI (`.github/
workflows/ci.yml`) führt die Testsuite bei jedem Push aus.
