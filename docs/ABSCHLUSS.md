# Projekt-Abschluss & Übergabe

Dieses Dokument fasst zusammen, was die **Software** kann (fertig), und was für
den **Betrieb einer echten Firma** noch bei dir liegt (kein Code).

> ⚠️ Der Abschnitt „Rechtliches/Steuern" ist **Orientierung, keine Rechts- oder
> Steuerberatung**. Die verbindliche Klärung machen Anwalt und Steuerberater.

---

## 1. Software – fertig ✅

Ein durchgängiger Kreislauf, alles lokal, kein Auto-Posting ohne deine Freigabe:

**Generieren → Prüfen → (Posten) → Messen → Verbessern**

| Schritt | Befehl |
|---|---|
| Content generieren | `python run.py --config brand_config.crypto.yaml --pillar news --platform youtube --count 1` |
| Günstiger Testlauf | `... --no-websearch --effort low` |
| Video zusammenbauen | `python assemble.py --platform youtube` → editieren → `--render` |
| Posten (nach Freigabe) | `python publish.py --platform youtube --live` |
| Video tracken | `python monitor.py add "<url>" --thema "..."` |
| Performance abrufen | `python monitor.py fetch` |
| Termin planen | `python schedule.py add <paket-datum> youtube "2026-07-20 09:00"` |
| Dashboard ansehen | `python dashboard.py --open` |
| Daten in Growth-Analyst | `python run.py ... --metrics monitoring/metrics.csv` |

Eingebaute Sicherheit: **Creative-Director-Freigabe** + **Compliance-Prüfer** +
automatischer **Disclaimer**; Posten blockt bei `⚠️ NACHBESSERN`/`⚠️ RISIKO`
(ohne `--force`). 111 automatische Tests, CI läuft.

---

## 2. Was noch bei dir liegt (kein Code)

### a) API-Zugänge eintragen (`.env`)
- [x] **YouTube-Monitoring** (`YOUTUBE_API_KEY`) – erledigt.
- [ ] **YouTube-Upload** (`YT_CLIENT_ID/SECRET/REFRESH_TOKEN`, OAuth) – erst nötig fürs Auto-Hochladen.
- [ ] **X** (`X_API_KEY/SECRET`, `X_ACCESS_TOKEN/SECRET`).
- [ ] **Facebook/Instagram** (`FB_PAGE_ID/ACCESS_TOKEN`, `IG_USER_ID/ACCESS_TOKEN`).

### b) Marke finalisieren
- [ ] `brand_config.crypto.yaml` ist auf „Anon Bitcoin News" gesetzt – Ton/Pillars bei Bedarf feinjustieren.
- [ ] Disclaimer-Text (in der Config) vom Anwalt prüfen lassen.

### c) Firma anmelden / absichern
- [ ] **Anwalt** (Medien-/IT-/Finanzrecht) beauftragen.
- [ ] **Steuerberater** beauftragen.
- [ ] **Buchhalter** (oft über den Steuerberater).
- [ ] Gewerbeanmeldung, Finanzamt-Anmeldung, Geschäftskonto.

---

## 3. Fragen für den Anwalt

1. **Anonymität vs. Impressumspflicht** (§ 5 DDG): Wie kann „Anon Bitcoin News"
   monetarisiert betrieben werden, ohne gegen die Impressumspflicht zu verstoßen?
   Welche ladungsfähige Anschrift ist nötig?
2. **BaFin/Anlageberatung**: Reicht mein „keine Anlageberatung"-Disclaimer, oder
   drohe ich als erlaubnispflichtige Finanzanalyse eingestuft zu werden? Wo ist die Grenze?
3. **MiCA / Krypto-Werbung**: Was muss ich bei Krypto-Content/Werbung beachten?
4. **Werbekennzeichnung**: Wie kennzeichne ich Kooperationen/Affiliate rechtssicher?
5. **Disclaimer prüfen**: Ist mein Disclaimer-Text (aus `brand_config.crypto.yaml`) ausreichend?
6. **Marken-/Namensschutz**: Kann/soll ich „Anon Bitcoin News" schützen? Kollisionen?
7. **KI-Inhalte**: Rechte/Lizenzen an KI-generierten B-Roll-Clips (fal.ai/Veo) und Musik?
8. **DSGVO**: Was brauche ich, falls Website/Newsletter/Kommentare dazukommen?

## 4. Fragen für den Steuerberater

1. **Rechtsform**: Einzelunternehmen/Kleinunternehmer vs. UG/GmbH – was passt steuerlich & bei der Haftung?
2. **Kleinunternehmerregelung** (§ 19 UStG): sinnvoll für den Start?
3. **Krypto-Besteuerung**: Wie werden Krypto-Einnahmen/-bestände behandelt (Haltefristen, „sonstige Einkünfte")?
4. **Einnahmearten**: YouTube-Monetarisierung, Sponsoring, Affiliate – wie versteuern?
5. **Betriebsausgaben**: Sind Tool-Kosten (Claude API, fal.ai, YouTube API) absetzbar? Belege wie sammeln?
6. **Buchhaltung**: EÜR ausreichend? Übernimmt das die Kanzlei oder brauche ich einen separaten Buchhalter?
7. **Anmeldung**: Welche Formulare beim Finanzamt/Gewerbeamt, in welcher Reihenfolge?

---

## 5. Empfohlene Reihenfolge

1. **Anwalt zuerst** – wegen Anonymität + Finanzthema (das ist der größte Risikopunkt).
2. Parallel: **Steuerberater** – Rechtsform + Anmeldung klären.
3. Erst danach **groß gehen** (viel posten, monetarisieren).

Die Software ist bereit und wartet – der Rest ist der Gang zu den Profis.
