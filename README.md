# „Du entscheidest“ – Cartoon-Studio

Ein lokales, weitgehend autonomes Studio für animierte 2D-Cartoon-Kurzserien
(TikTok / YouTube Shorts, 1080 × 1920, 30 fps, 30–60 s). Es nutzt keine externen
KI-Generatoren (kein Runway, Kling, ElevenLabs …): Bild, Animation, Stimmen, Musik,
Geräusche, Untertitel, Schnitt und Qualitätskontrolle laufen mit Open-Source-Software
auf der CPU.

```
bash setup.sh                          # Werkzeuge, Stimmen, Schriften installieren + Systemprüfung
python -m studio produce wohnung-4b-e01   # produzieren + QC (+ bis zu 3 Korrekturen)
python -m studio dashboard             # dashboard/index.html
```

## Wer macht was?

| Aufgabe | Umsetzung |
|---|---|
| Geschichten, Dialoge, Regie, neue Figuren | Claude (tägliche geplante Sitzung, siehe `docs/AUTOPILOT.md`) |
| Zeichnungen & Animation | eigene Vektor-Engine (Cairo): Zentralperspektive-Kulissen, parametrische Figuren, POV-Hände, Lippensynchronität aus der Lautstärke, Blinzeln, Gesten, Kamerafahrten, Weitwinkel-/Türspion-Linse (OpenCV) |
| Stimmen | Qwen3-TTS 1.7B Base (lokal, Apache-2.0, Stimmklon aus freien Referenzen; Sieger im Blindtest) – Rückfall automatisch auf ZONOS3-Mini (Emotions-Regler), dann Piper; Effekte per ffmpeg |
| Musik & Geräusche | algorithmisch erzeugt (NumPy) – keine Fremd-Samples, lizenzfrei |
| Untertitel | ASS, häppchenweise im Kurzvideo-Stil, farbig je Figur |
| Schnitt & Export | ffmpeg (H.264 High, AAC, −14 LUFS, faststart) |
| Qualitätskontrolle | `studio/qc.py`: 7 Kategorien, 0–100 Punkte, Whisper hört jede Zeile ab |
| Veröffentlichung | YouTube Data API v3; TikTok Content Posting API (Entwurf ins Postfach, gepostet wird in der App); Buffer-API eingerichtet, aber abgeschaltet (0 Aufrufe) |
| Abstimmungen | YouTube-Kommentare automatisch; TikTok manuell (siehe Grenzen) |
| Dashboard | `dashboard/index.html` |

## Aufbau

```
studio/
  draw/       prims, persp (3D->2D), characters, sets, pov, overlays
  audio/      tts (Qwen3 → ZONOS3 → Piper), qwen_worker, sfx, music
  scene.py    Frame-Compositor     timeline.py  Drehbuch -> Zeitleiste
  render.py   Video/Ton/Endschnitt subtitles.py ASS-Untertitel
  qc.py       Qualitätskontrolle   pipeline.py  Produktion mit Korrekturschleife
  release.py  Freigabe/Upload/Abstimmung        publish/ youtube, tiktok, votes
  dashboard.py, selfcheck.py, validate.py, voicecast.py, modelsheet.py
db/characters/  Figuren (+ Model-Sheets *_sheet.png)    db/series/  Serienbibeln
episodes/<id>/  script.json, final.mp4, cover.jpg, qc_report.md, qc_contact.png, status.json
config/studio.json   Veröffentlichung, Qualität, Zeitplan   (config/secrets/ = Zugangsdaten, nicht im Git)
docs/           DREHBUCH_FORMAT.md, AUTOPILOT.md, GRENZEN.md
```

## Sicherheitsriegel vor jeder Veröffentlichung
1. QC ≥ 90 Punkte und keine kritischen Fehler (sonst max. 3 automatische Korrekturen, danach gesperrt)
2. Freigabe (`python -m studio approve <id>`), solange `require_manual_approval = true`
3. `publishing.enabled = true` + gültige Zugangsdaten
4. Kennzeichnung als KI-generiert auf beiden Plattformen

Ehrliche Grenzen: siehe `docs/GRENZEN.md`.
