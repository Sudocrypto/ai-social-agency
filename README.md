# AI Social Media Agency — "Danilo Takes Off"

Ein Multi-Agent-System in Python, das wie eine komplette Social-Media-Agentur
funktioniert: spezialisierte KI-Agents ("Mitarbeiter") produzieren gemeinsam
fertigen Content für X, Instagram, Facebook und YouTube – inkl. Briefings für
KI-Video-Clips. **Phase 1:** Content wird generiert und zur Freigabe exportiert
(kein automatisches Posten).

## Setup

Braucht **Python 3.10+**. Auf macOS ist `python` oft noch das alte System-Python
2.7 – benutze `python3`. Hinweis für die macOS-`zsh`: **keine `# …`-Kommentare in
Befehle pasten** (zsh behandelt `#` interaktiv nicht als Kommentar).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Danach `.env` öffnen (`nano .env` oder `open -e .env`) und `ANTHROPIC_API_KEY`
eintragen (`FAL_KEY` optional). `.env` wird nie committet, Keys stehen nur dort.
Im aktiven venv ist `python` dann Python 3 – die Beispiele unten funktionieren.

### Preflight-Check (empfohlen vor dem ersten Lauf)

Prüft Keys, Pakete (`fal-client`), `ffmpeg`, Config und Video-Budget – **bevor**
ein teurer Lauf startet, statt mittendrin zu scheitern:

```bash
python doctor.py --config brand_config.ki.yaml
```

Gibt pro Punkt ✅/⚠️/❌ mit konkretem Fix-Hinweis. Exit-Code 1 nur bei harten
Fehlern (fehlender Key, unbekanntes Modell). Für echtes Video brauchst du
zusätzlich `pip install fal-client` und `ffmpeg` (`brew install ffmpeg`).

## Nutzung

```bash
python run.py --pillar auswandern --platform all --count 5
python run.py --pillar reise --platform instagram --topic "Erster Monat Thailand"
python run.py --pillar auswandern --no-websearch
python run.py --pillar auswandern --render-video
```

(`--no-websearch` = kostenloser Testlauf ohne Live-Websuche; `--render-video` =
echte fal.ai-Clips statt Dry-Run.)

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
| `--effort` | `low`/`medium`/`high`/`xhigh`/`max` für ALLE Agents (Kosten/Qualität); überstimmt die Config |

Konfiguration (Marke, Modelle, Video-Modus, Kosten-Cap): **`brand_config.yaml`**.

**Kosten/Qualität steuern:** Jeder Agent hat eine `effort`-Stufe
(`low`→`max`, mehr = teurer & gründlicher). In `brand_config.yaml` unter `effort`
pro Agent einstellbar (kreative Agents hoch, mechanische wie SEO/Publisher
niedriger). Für einen günstigen Draft-Lauf alles global drosseln:
`python run.py --pillar auswandern --platform instagram --effort low`. Ein
typischer Voll-Lauf kostet grob 0,10–0,35 $ (steht am Ende in `review.md`).

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
python publish.py
python publish.py --date 2026-07-14 --platform x
python publish.py --platform facebook --live
python publish.py --platform instagram --ig-media-url https://.../reel.mp4 --live
python publish.py --platform youtube --yt-video /pfad/final.mp4 --live
```

Ohne Argumente: neuestes Paket, Dry-Run, alle Plattformen. `--live` postet echt
(mit Rückfrage pro Plattform).

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

**Freigabe & Compliance werden durchgesetzt:** `publish.py` liest die Bewertung
des Creative Directors (`director_review.md`) **und** den Compliance-Report
(`compliance_report.md`). Plattformen, die als `⚠️ NACHBESSERN` bzw. mit
`⚠️ RISIKO` markiert sind, werden **nicht** gepostet – es sei denn, du überstimmst
mit `--force`. So sind Freigabe-Instanz und rechtliche Prüfung auch beim Posten
wirksam.

## Video-Assembly (optional)

Baut aus dem Post-Production-Schnittplan eine fertige `.mp4` – dein iPhone-Material
+ KI-B-Roll aneinandergehängt, Untertitel eingebrannt, Musik untergemischt (via
**ffmpeg**). Der eigentliche Render läuft lokal (ffmpeg installiert).

```bash
python assemble.py --platform youtube
python assemble.py --platform youtube
python assemble.py --platform youtube --render
python assemble.py --platform instagram --scaffold
```

Ablauf: 1. Aufruf legt ein editierbares `assembly.json` an → darin eigene
Clip-Pfade, Timings, Untertitel und `MUSIK.mp3` eintragen. 2. Aufruf (Dry-Run)
zeigt das ffmpeg-Kommando + schreibt die SRT. 3. Mit `--render` entsteht
`final.mp4`. `--scaffold` erzeugt das `assembly.json` neu.

`assembly.json` (pro Plattform, in `output/{datum}/{plattform}/`) beschreibt jedes
Segment (`source`, `start`, `end`, `subtitle`, `mute`), Musik (`gain_db`) und das
Zielformat (YouTube 1920×1080, sonst 1080×1920). Stumme Segmente (KI-B-Roll)
bekommen automatisch Stille; die Musik läuft leiser darunter. Der Scaffold
übernimmt die generierten B-Roll-Clips und verteilt die Untertitel aus dem
Schnitt-Briefing – du fügst nur dein eigenes Material und die Musikdatei ein.

## Voll-Automatik (`auto.py`)

Ein Befehl, der die ganze Kette verkettet: **Content generieren → Freigabe- &
Compliance-Check → KI-Video rendern → zusammenschneiden → hochladen → tracken.**

```bash
python auto.py --config brand_config.crypto.yaml --pillar news --topic "Bitcoin ETF"
python auto.py --config brand_config.crypto.yaml --pillar news --topic "Bitcoin ETF" --post
```

Die Automatik macht **so viel wie möglich** und stoppt sauber, sobald etwas fehlt:
- ohne `FAL_KEY` → nur Text/Skript (kein KI-Video),
- ohne `ffmpeg` → Clips liegen bereit, aber kein Schnitt,
- ohne `--post` → Video wird gerendert, aber **nicht** hochgeladen,
- ohne YouTube-OAuth → Upload wird sauber abgebrochen.

**Sicherheits-Gate:** Alles, was der Creative Director (`⚠️ NACHBESSERN`) oder der
Compliance-Prüfer (`⚠️ RISIKO`) markiert, wird **nicht** hochgeladen (nur mit
`--force` überstimmbar – nicht empfohlen). Der Upload passiert ausschließlich mit
`--post`.

> ⚠️ **Finanz-/Krypto-Content nicht unbeaufsichtigt auto-posten**, bevor ein
> Anwalt Disclaimer und Konzept geprüft hat. Bis dahin ohne `--post` fahren
> (Video fertig, Upload manuell nach Sichtprüfung).

## Dashboard

Eine lokale HTML-Übersicht (kein Server, kein Netz) über den ganzen Betrieb:
erzeugte Pakete mit Freigabe-/Compliance-Status (Bereit/Blockiert/Gepostet),
was gepostet wurde und die YouTube-Performance.

```bash
python dashboard.py
python dashboard.py --open
```

Schreibt `dashboard.html` (im Browser öffnen bzw. `--open` auf macOS). Der
Status je Plattform ergibt sich aus dem Director-Urteil, dem Compliance-Report
und dem Post-Log (`monitoring/post_log.json`, das `publish.py --live`
automatisch füllt). Einfach neu ausführen, um zu aktualisieren.

**Termine planen** (erscheinen im Dashboard unter „Als Nächstes geplant"):

```bash
python schedule.py add 2026-07-20 youtube "2026-07-20 09:00" --note "Bitcoin ETF"
python schedule.py list
python schedule.py remove 0
```

Ein Termin ist eine Erinnerung – es wird **nichts automatisch gepostet**; das
machst du bewusst per `publish.py`.

## Monitoring / Performance-Überwachung

Verfolgt, wie gut veröffentlichte YouTube-Videos ankommen, und schließt die
Schleife zurück zum Growth-Analysten. Braucht nur einen **YouTube-Data-API-Key**
(kein OAuth) für öffentliche Video-Stats.

```bash
python monitor.py add "https://youtu.be/XXXXXXXXXXX" --thema "Bitcoin ETF"
python monitor.py list
python monitor.py fetch
python monitor.py remove XXXXXXXXXXX
python monitor.py clear
```

`fetch` ruft Views/Likes/Kommentare ab und schreibt `monitoring/report.md`
(Ranking, Engagement, beste/schwächste Videos) sowie `monitoring/metrics.csv`.
Diese CSV steckst du direkt in den Growth-Analysten:

```bash
python run.py --config brand_config.crypto.yaml --pillar news --platform youtube --metrics monitoring/metrics.csv
```

So wird aus „was lief gut" ein datengetriebener Plan für die nächste Runde.
`YOUTUBE_API_KEY` kommt in die `.env` (Google Cloud Console → YouTube Data API v3
→ API-Key). Die `monitoring/`-Daten bleiben lokal (gitignored).

## Mehrere Marken & Compliance-Modus

Über `--config` lässt sich eine beliebige Marken-Datei laden – so betreibst du
mehrere Marken mit einem System:

```bash
python run.py --config brand_config.crypto.yaml --pillar basics --platform instagram --count 1
```

Die mitgelieferte Vorlage **`brand_config.crypto.yaml`** ist eine Bitcoin-/
Investment-Marke mit **Compliance-Leitplanken**. Ist im Config-Block
`compliance:` `enabled: true` gesetzt, dann:

- werden die `regeln` in **jeden** Agent-System-Prompt eingespeist (keine konkrete
  Anlageberatung, keine garantierten Renditen, kein FOMO, Werbung kennzeichnen …),
- wird der `disclaimer` **automatisch an jeden `post.md` angehängt**,
- läuft ein **Compliance-Prüfer-Agent**: er scannt die finalen Posts auf riskante
  Formulierungen, schreibt `compliance_report.md` und meldet Risiken an den
  Creative Director, der bei `⚠️ RISIKO` nachbessern lässt (nur im Compliance-Modus
  aktiv – bei normalen Marken übersprungen, kein Extra-Aufruf/Kosten).

> ⚠️ **Kein Rechtsersatz.** Der Compliance-Modus senkt Risiko, macht dich aber
> nicht rechtlich unangreifbar und ersetzt keine Rechtsberatung. Lass Marke +
> Disclaimer einmal anwaltlich prüfen (in DE/EU u. a. BaFin, MiCA,
> Anlageberatung/Finanzanalyse, Werbekennzeichnung). Passe `disclaimer`/`regeln`
> an deinen Fall an.

## Tests

Offline-Regressionssuite (gestubbtes LLM, kein API-Key nötig):

```bash
pip install -r requirements-dev.txt
pytest
```

Deckt ab: Modell-Routing (Opus/Sonnet), Plattform-Split, SEO-Parsing in
`meta.json`, Video-Prompt-Parsing + Kosten-Cap und die komplette
Output-Struktur.

## Abschluss & Übergabe

Was fertig ist und was für den echten Firmenbetrieb noch bei dir liegt (API-Tokens,
Anwalt, Steuerberater) – inkl. fertiger Fragenlisten für die Termine:
**[`docs/ABSCHLUSS.md`](docs/ABSCHLUSS.md)**.

## Architektur

Transparente Pipeline (`agency/pipeline.py`) – kein Blackbox-Framework. Jeder
Agent ist ein eigenes Modul unter `agency/agents/` mit eigenem System-Prompt und
klarer Rolle. Der `RunContext` (`agency/context.py`) trägt alle Zwischenergebnisse
und das Kosten-Log durch die Pipeline. Standard ist sequenzielle Ausführung
(maximal debugbar); mit `--parallel` laufen unabhängige Agents je Abhängigkeits-
Ebene (`agency/graph.py`) gleichzeitig – Ergebnis identisch. CI (`.github/
workflows/ci.yml`) führt die Testsuite bei jedem Push aus.
