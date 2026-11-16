# Drehbuch-Format (`episodes/<id>/script.json`)

Ein Drehbuch ist eine Liste von **Einstellungen** (`shots`). Die Dauer jeder Einstellung ergibt
sich automatisch aus der Länge der gesprochenen Zeilen. Vor der Produktion prüft
`python -m studio validate <id>` alle Felder.

```jsonc
{
  "id": "wohnung-4b-e02", "series": "wohnung-4b", "episode": 2,
  "title": "Der Schlüssel", "label": "WOHNUNG 4B · TEIL 2",
  "summary": "Ein Satz für Dashboard und Serienbibel.",
  "cliffhanger": {"question": "…?", "options": {"A": "…", "B": "…"}},
  "cover_shot": 3,                       // Einstellung für das Vorschaubild
  "publish": {"title": "…", "description": "…", "hashtags": ["#…"]},
  "shots": [ { …Einstellung… } ]
}
```

## Einstellung

| Feld | Werte | Bedeutung |
|---|---|---|
| `set` | `flur`, `wohnzimmer`, `treppenhaus`, `schlafzimmer` | Kulisse |
| `time` | `day` / `night` | Lichtstimmung |
| `variant` | `feet` (flur), `open` / `flicker` (treppenhaus) | Kulissen-Variante |
| `zoom` | 1.0 – 3.0 | Brennweite (1 = Weitwinkel-POV, 3 = Nahaufnahme) |
| `lens` | 0 – 0.5 | Weitwinkel-/Türspion-Verzerrung (0.06–0.1 normal, 0.35+ Türspion) |
| `camera` | `{"move": "static/push_in/zoom_out/pan_left/pan_right/tilt_down", "strength": 1, "punch": [s], "shake": [s]}` | Kamera |
| `characters` | `[{"id", "spot" oder "x"/"z", "expr", "arms", "prop", "look", "enter": "left/right", "approach": m, "silhouette": bool}]` | Figuren im Bild |
| `pov` | `{"mode": "phone/door/box/table/knock", …}` | eigene Hände (Ich-Perspektive) |
| `lines` | `[{"speaker", "text", "emotion", "expr", "arms", "fx", "delay", "gap", "tts", "no_sub"}]` | Dialog |
| `sfx` | `[{"name", "at", "gain"}]` | knock, knock_hard, creak, buzz, ping, whoosh, sting, heartbeat, steps, thud, lights_out, keys, riser |
| `music` | `tension`, `mystery`, `cozy`, `comedy`, `silence` | Musikstimmung |
| `caption` | Text | große Comic-Einblendung („03:07 UHR“) |
| `peephole` | bool | Türspion-Maske |
| `blackout_at` | Sekunden | Licht aus → Schwarzbild (von der QC erlaubt) |
| `endcard` | `{"question", "options": {"A","B"}, "cta", "next"}` | Abstimmungs-Endkarte (Pflicht in der letzten Einstellung) |
| `pad_start`, `pad_end`, `min_dur`, `dur` | Sekunden | Timing-Feinschliff |

**Ausdrücke (`expr`)**: neutral, happy, angry, scared, surprised, suspicious, sad, smirk, creepy
**Armhaltungen (`arms`)**: down, hips, wave, point, hold, shrug, keys, raise, cross
**Requisiten (`prop`)**: cake, box, keys, letter, phone
**Stimm-Effekte (`fx`)**: door (durch die Tür), phone, inner (innerer Monolog), radio
**Emotionen (`emotion`)**: wirken bei Figuren mit Emotions-Stimme (Ich-Erzähler): neutral, whisper, surprised, scared, happy, angry

## Handy-Chat (`pov.mode = "phone"`)
```json
{"mode": "phone", "contact": "Lina", "avatar": "#c4473a",
 "messages": [{"from": "du", "text": "…", "at": 0.3}, {"from": "lina", "text": "…", "at": 1.9}]}
```

## Dramaturgie-Regeln (werden von der QC geprüft)
- Hook in der ersten Sekunde (Einblendung, Geräusch oder Satz)
- Gesamtlänge 30–60 s, Einstellungen 1–8,5 s
- Zeilen höchstens 22 Wörter
- Letzte Einstellung: A/B-Abstimmung + „Teil X folgt“
