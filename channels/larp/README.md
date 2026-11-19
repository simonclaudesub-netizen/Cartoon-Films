# Kanal 2: „VEKTOR · agent ops" – KI-Agent-LARP-Edits

Kurze Hochkant-Edits (15–25 s) im Stil der „Claude/AI-Agent"-LARP-Videos: dichte Neon-HUD-Dashboards,
leuchtende Datenstränge, rotierender Strahlenkern, live hochzählende Zahlen, Schnitte genau auf dem Beat.
Alles prozedural gerendert (Cairo + NumPy + ffmpeg), keine KI-Bildgeneratoren, keine fremden Assets.

```
python -m larp render test-01          # -> channels/larp/out/test-01/final.mp4, cover.jpg, tiktok.txt
python -m larp still test-01 9.0 x.png # Einzelbild zum Prüfen
```

## Szenen (`larp/scenes.py`)
| Szene | Vorbild aus den Referenzen |
|---|---|
| `agent_ops` | Panel-Reihe oben, Strang-Netz, 3D-Strahlenkern in der Mitte, STREAM/DISPATCH/FORMULAS/OUTPUT unten |
| `pipeline` | DECISION PIPELINE: Kennzahl-Kacheln, 3 Karten-Spalten mit Lichtfasern, Use-Case-Raster, Run-Log, Guardrails |
| `mono_field` | CONFIDENCE FIELD · MONO: Partikelfluss mit Pixelstaub, GATE-0.85-Linie, Code-Editor tippt, Router/Latenz |
| `trading` | Trading Desk: pinker Partikel-Wirbel, Agenten-Leiste, Markt/Orderbuch, Evidenz-Matrix, Live-Log (nur Paper/Sim) |
| `core_card` | Endkarte mit Kern + Systemname |

## Video-Spezifikation (`videos/<id>.json`)
`bpm`, `drop_beat`, `caption`, `sound` und `shots` (je `scene`, `beats`, Kamera `cam.from/to = [x, y, zoom]`,
optional `text` + `text_y`). Jede Einstellung dauert ganze Schläge → jeder Schnitt landet auf dem Beat.

## Musik
Die Wunsch-Sounds („KITTY RALLY TWO - SLOW", „Gorąca Jak San Pedro") sind geschützt und werden **in der
TikTok-App** daruntergelegt (Sound verwenden → Originalton 0 %). Im Video steckt ein eigener, lizenzfreier
Phonk-Platzhalter (`larp/beat.py`) im selben Tempo. Wer eine eigene, lizenzierte Audiodatei hat:
`python -m larp render test-01 --audio datei.mp3 --audio-offset 12.5`.

## Ehrlichkeit
Alle Werte sind ausgedacht; im Bild steht immer „metrics illustrative / simulated", Trading nur „paper".
Kein echtes Firmenlogo oder -name im Bild – das System heißt VEKTOR. Beim Posten „KI-generiert" kennzeichnen.
