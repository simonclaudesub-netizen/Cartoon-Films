# Autopilot – täglicher Ablauf

Diese Datei ist die Arbeitsanweisung für die tägliche, geplante Claude-Sitzung
(„Writers' Room + Regie“). Claude übernimmt die kreative Arbeit (Geschichte, Dialoge,
Regie, Sichtprüfung); alles andere erledigt die lokale Pipeline.

## Ablauf (jeden Tag, Start ca. 14:20 Uhr deutscher Zeit)

0. **Arbeitsplatz**: Repository klonen (falls nicht vorhanden), `bash setup.sh` ausführen
   (installiert Werkzeuge, Qwen3-TTS samt Modell, ZONOS3, Whisper – beim ersten Mal ca. 15 Minuten;
   bricht nie ab, sondern meldet WARNUNG-Zeilen; `python -m studio check` zeigt, was fehlt).
   YouTube-Zugang kommt aus den Umgebungsvariablen `YT_CLIENT_ID`, `YT_CLIENT_SECRET`,
   `YT_REFRESH_TOKEN` der Cloud-Umgebung (nie ins Repository schreiben).
   TikTok-Zugang (falls eingerichtet) aus `TT_CLIENT_KEY`, `TT_CLIENT_SECRET`, `TT_REFRESH_TOKEN`,
   `TT_TOKEN_KEY`; ein von TikTok erneuerter Token liegt verschlüsselt in `config/tiktok_token.enc`
   und muss mit committet werden.
1. **Systemprüfung**: `python -m studio check` – bei fehlenden Pflicht-Werkzeugen erneut `bash setup.sh`.
2. **Stimmen einsammeln** für die letzte veröffentlichte Episode:
   `python -m studio votes <letzte-episode>`
   (YouTube automatisch; TikTok nur, wenn `episodes/<id>/tiktok_comments.txt` importiert wurde).
3. **Serienbibel lesen**: `db/series/<serie>.json` – Logline, Weltregeln, Geheimnisse, `next_plans`,
   bisherige Abstimmungen. Gewinner-Option der Abstimmung bestimmt die Handlung.
   Bei Gleichstand/keinen Stimmen: die spannendere Option wählen und im Log begründen.
3b. **Zuschauer-Wünsche lesen**: `python -m studio.publish.comments wuensche <letzte-episode>` →
   `stats/wuensche_<id>.json` (alle Kommentare, auch Ideen, „beides“, „C: …“, Theorien, Antworten des Kanals).
   Pro Folge **eine** passende Idee als kleine Anspielung einbauen (Zeile, Requisit, Gag oder Figur-Reaktion),
   bevorzugt die mit den meisten Likes bzw. eine, der der Kanal „schreibe ich mir auf“ geantwortet hat:
   - Die Gewinner-Option bleibt die Handlung – Wünsche ergänzen, entscheiden aber nie gegen die Abstimmung.
   - Familientauglich umdeuten (z. B. „Tretmine“ → harmlose Falle aus Krimskrams), keine Gewalt, keine
     realen Personen/Marken, keine Benutzernamen im Video, nichts, was Weltregeln oder Geheimnisse bricht.
   - „Beides“-Kommentare (A und B zugleich) dürfen als Augenzwinkern vorkommen („Beide wecken? Keine Chance.“).
   - Passt keine Idee, keine einbauen. Verwendete Idee in der Serienbibel unter `zuschauer_ideen`
     eintragen (Folge + Idee in eigenen Worten) und im Kurzbericht nennen.
4. **Entwurf vorhanden?** Liegen `episodes/<id>/entwurf_A.json` / `entwurf_B.json` vor, wird der Entwurf
   der Gewinner-Option übernommen: `python -m studio entwurf <id> <A|B>` (dann weiter mit Schritt 5).
   Sonst: **Drehbuch schreiben**: `episodes/<serie>-eNN/script.json` nach `docs/DREHBUCH_FORMAT.md`.
   - Eigene, originelle Handlung; keine realen Personen, Marken oder fremden Figuren.
   - Hook in Sekunde 1, 30–60 s, Cliffhanger + A/B-Abstimmung.
   - Neue Figuren: zuerst in `db/characters/<id>.json` anlegen, Stimme mit
     `python -m studio.voicecast <id> --female|--male` casten, `python -m studio sheets`.
   - Serienbibel aktualisieren: neue Geheimnisse, `next_plans` für A und B der neuen Folge.
5. **Prüfen & produzieren**: `python -m studio validate <id>` → `python -m studio produce <id>`
   (inkl. automatischer QC und bis zu 3 Korrekturversuchen).
6. **Sichtprüfung durch Claude**: `episodes/<id>/qc_contact.png` ansehen und `qc_report.md` lesen.
   Bei sichtbaren Fehlern (Figur abgeschnitten, Text überdeckt, unlogische Szene) Drehbuch
   korrigieren und erneut produzieren (zählt zu den 3 Versuchen).
   **Selbstheilung ohne Rückfrage** (Kanalinhaber, 18.11.2026: „komplett automatisch“): Wird die
   Episode abgelehnt, NICHT beim Menschen nachfragen, sondern selbst reparieren und erneut
   `python -m studio produce <id>` starten – bis zu 2 weitere Runden:
   - Sprachzeilen (`qc_report.md` → „Muss korrigiert werden“): Zeile im `script.json` umformulieren,
     gleicher Sinn, aber ohne Ziffern/Zahlwörter, Abkürzungen und verschluckbare Endungen
     („bin's“ → „bin es“); geflüsterte Ein-Wort-Sätze notfalls `emotion` „scared“ statt „whisper“.
     Untertitel und Folgezeilen, die den Wortlaut zitieren, mitändern. `entwurf_*.json` nicht anfassen.
   - Liegt der Fehler in der Prüfung selbst (Stimme korrekt, Whisper schreibt nur anders), den
     Abgleich in `studio/qc.py` korrigieren, Test ergänzen, `python3 tests/test_studio.py`.
     Nur die Text-Normalisierung darf geändert werden – Grenzwerte (`PASS_SCORE`, `LINE_MIN`,
     `line_min`) und Prüfungen nie lockern oder entfernen; der Test muss zeigen, dass echte
     Sprechfehler weiter durchfallen. Die Änderung im Kurzbericht nennen.
   - Erst wenn auch Runde 3 scheitert, nicht veröffentlichen und den Grund im Kurzbericht nennen.
   Die Zeitgrenze (Upload vor 17:40) gilt weiter; sonst Termin am Folgetag.
7. **Freigabe**: Der Kanalinhaber hat entschieden (16.11.2026): bestandene QC (≥ 90, keine kritischen
   Fehler) gilt als Freigabe (`require_manual_approval = false`, Status „freigegeben“ durch
   „qc-automatik“). Findet die Sichtprüfung in Schritt 6 einen Fehler, wird NICHT veröffentlicht,
   bevor er behoben ist.
8. **Veröffentlichen**:
   - YouTube automatisch: `python -m studio publish <id> --platform youtube`. Das Video wird sofort
     hochgeladen und von YouTube um **18:00 Uhr (Europe/Berlin)** freigeschaltet (`publishAt`);
     ist es später als 17:40, wird es für 18:00 Uhr am Folgetag eingeplant (nie sofort).
   - Neue Folge nur produzieren, wenn die vorige Folge bereits öffentlich ist (sonst gibt es noch keine Abstimmung) – dann nur Kurzbericht „wartet auf Abstimmung“.
   - TikTok **als Entwurf ins Postfach** (`config/studio.json` → `tiktok.mode = "entwurf"`):
     `python -m studio publish <id> --platform tiktok` (nach YouTube). Der Mensch postet um 18:00 Uhr in der
     TikTok-App (Posteingang → Systembenachrichtigungen) mit „KI-generierte Inhalte“. Im Kurzbericht den
     fertigen Text aus `published.tiktok.caption` zum Kopieren angeben und ans Posten um 18 Uhr erinnern.
     Grund (17.11.2026): Über Buffer gepostete Videos waren öffentlich, bekamen aber 0 Aufrufe. Buffer
     nicht wieder einschalten, außer der Kanalinhaber verlangt es (`mode = "buffer"`).
     Geht der Entwurf nicht: `python -m studio tiktok-paket <id>` und `final.mp4` + `tiktok_upload.txt`
     per Datei-Versand schicken; nach dem Posten `python -m studio manuell-gepostet <id> tiktok <url>`.
     (Eigene TikTok-App darf laut TikTok-Richtlinien nicht direkt posten – nicht versuchen.)
9. **Dashboard** aktualisieren: `python -m studio dashboard`; Änderungen committen und pushen
   (`final.mp4` ist absichtlich nicht im Git).
10. **Kurzbericht** als letzte Nachricht: Folge, QC-Wert, YouTube-Link, Abstimmungsergebnis der
    Vorfolge. Bei Ablehnung oder Fehler: klar sagen, was fehlt (z. B. abgelaufener YouTube-Zugang →
    Mensch muss `python -m studio auth-youtube` neu durchlaufen).

## Harte Regeln
- Nie veröffentlichen ohne bestandene QC (≥ 90, keine kritischen Fehler).
- Nie Zugangsdaten ins Repository schreiben (`config/secrets/` ist ignoriert).
- Keine kostenpflichtigen Dienste, keine externen KI-Generatoren.
- Jedes Video wird als KI-generiert gekennzeichnet (YouTube `containsSyntheticMedia`, TikTok `is_aigc`).
- Fehler ins Log (`logs/studio.log`) und, wenn nicht selbst behebbar, im Dashboard sichtbar lassen.
