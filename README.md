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
| `--metrics` | Performance-Daten (CSV/TSV/JSON) für datengetriebene Growth-Analyse |

Konfiguration (Marke, Modelle, Video-Modus, Kosten-Cap): **`brand_config.yaml`**.

**Datengetriebene Optimierung:** Mit `--metrics daten.csv` (oder `.json`) bekommt
der Growth-Analyst echte Performance-Zahlen (Impressions, Likes, Watchtime …) und
analysiert konkret, was lief und was floppte, statt nur Baseline-KPIs zu nennen.
Er erkennt eine `plattform`-Spalte und bildet Summen pro Plattform.

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

## Phase 2: Auto-Posting (optional)

Freigegebenen Content aus einem Review-Paket per API posten. **Standard ist
Dry-Run** (nur Validierung + Vorschau, kein Netz). Echtes Posten braucht `--live`
und eine Bestätigung pro Plattform (`JA`) – es ist nach außen wirksam und nicht
umkehrbar.

```bash
python publish.py                                   # neuestes Paket, Dry-Run, alle Plattformen
python publish.py --date 2026-07-14 --platform x
python publish.py --platform facebook --live        # echt posten (mit Rückfrage)
python publish.py --platform instagram --ig-media-url https://.../reel.mp4 --live
python publish.py --platform youtube --yt-video /pfad/final.mp4 --live
```

Zugangsdaten kommen aus `.env` (Vorlage in `.env.example`): X API v2 (OAuth 1.0a),
Meta Graph (Facebook-Seite + Instagram-Business), YouTube Data API v3 (OAuth2).

| Plattform | Posten | Besonderheit |
|---|---|---|
| X (Twitter) | Text/Thread | via `tweepy` (optional) |
| Facebook | Text | direkter Graph-Call |
| Instagram | Bild/Reel | braucht **öffentlich gehostete** Medien-URL (`--ig-media-url`) |
| YouTube | Video-Upload | braucht **fertige Videodatei** (`--yt-video`); startet auf *privat* |

Instagram und YouTube liefern im Dry-Run bewusst einen Validierungsfehler, solange
kein gehostetes Medium bzw. kein fertiges Video übergeben wird – so postet nichts
Unvollständiges. Optionale Live-Abhängigkeiten: `tweepy` (X),
`google-api-python-client google-auth google-auth-oauthlib` (YouTube).

**Freigabe wird durchgesetzt:** `publish.py` liest die Bewertung des Creative
Directors (`director_review.md`) und postet Plattformen, die er als
`⚠️ NACHBESSERN` markiert hat, **nicht** – es sei denn, du überstimmst mit
`--force`. So ist die „finale Freigabe-Instanz" auch beim Posten wirksam.

## Video-Assembly (optional)

Baut aus dem Post-Production-Schnittplan eine fertige `.mp4` – dein iPhone-Material
+ KI-B-Roll aneinandergehängt, Untertitel eingebrannt, Musik untergemischt (via
**ffmpeg**). Der eigentliche Render läuft lokal (ffmpeg installiert).

```bash
python assemble.py --platform youtube               # 1) legt editierbares assembly.json an
#   -> assembly.json bearbeiten: eigene Clip-Pfade, Timings, Untertitel, MUSIK.mp3
python assemble.py --platform youtube               # 2) Dry-Run: zeigt ffmpeg-Kommando + SRT
python assemble.py --platform youtube --render      # 3) rendert final.mp4
python assemble.py --platform instagram --scaffold  # assembly.json neu erzeugen
```

`assembly.json` (pro Plattform, in `output/{datum}/{plattform}/`) beschreibt jedes
Segment (`source`, `start`, `end`, `subtitle`, `mute`), Musik (`gain_db`) und das
Zielformat (YouTube 1920×1080, sonst 1080×1920). Stumme Segmente (KI-B-Roll)
bekommen automatisch Stille; die Musik läuft leiser darunter. Der Scaffold
übernimmt die generierten B-Roll-Clips und verteilt die Untertitel aus dem
Schnitt-Briefing – du fügst nur dein eigenes Material und die Musikdatei ein.

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
