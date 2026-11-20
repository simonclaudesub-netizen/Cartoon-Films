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
- Letzte Einstellung: A/B-Abstimmung + „Teil X folgt“. Die Frage (`endcard.question`) einzeilig halten
  (z. B. „WAS SOLL ICH TUN?“) – nur dann passt der Hinweis „ALLE TEILE AUF MEINEM PROFIL“ (`more`, Standard;
  `"more": ""` schaltet ihn ab) noch in den sicheren Bereich.

## Einstieg für Neue (Kanalinhaber, 20.11.2026)
Die meisten Zuschauer kommen aus dem Feed und kennen die Vorfolgen nicht. Daten bis Teil 4: Teil 1 und 4
(Einstieg ohne Vorwissen verständlich) liefen am besten; Teil 2 und 3 begannen mit „Ihr habt B/A gewählt“
und Teil 3 lief auf YouTube am schwächsten.
- **Erste Einstellung (≤ 3 s) muss ohne Vorwissen funktionieren:** Ausgangslage + Widerspruch in einem
  Satz, mit konkretem Detail (Uhrzeit, Zahl, Ort). Beispiel Teil 4: „Wenn Lina zu Hause im Bett liegt,
  wer steht dann vor meiner Tür?“ + Einblendung „300 KM WEG?!“.
- **Nicht** mit dem Abstimmungsergebnis, „wie ihr wisst“ oder einer Rückschau anfangen. Das Ergebnis
  („Ihr habt A gewählt“) kommt kurz in Einstellung 2 oder als kleine Einblendung – nie als Hook.
- Figuren beim ersten Nennen mit Rolle: „meine Freundin Lina“, „der Nachbar Okan“.
- Einblendung (`caption`) der ersten Einstellung = das Rätsel in 2–4 Wörtern, nicht „TEIL 5“.
- **Titel** (`publish.title`): verständlich ohne Vorfolgen – konkrete Situation + offene Frage/Widerspruch
  + ein Emoji, Serie und Teil am Ende („… | Wohnung 4B – Teil N“). Hook-Satz und Titel dürfen sich ähneln.
