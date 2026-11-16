# QC-Bericht – Versuch 3

**Gesamt: 59 / 100** – NICHT BESTANDEN (Mindestwert 90)

**Kritische Fehler:**
- technik: Dauer 30-60 s (81.0 s)

| Kategorie | Punkte |
|---|---|
| technik | 11 / 15 |
| ton | 15 / 15 |
| stimmen | 17.99 / 20 |
| bild | 15 / 15 |
| konsistenz | 10 / 10 |
| story | 13 / 15 |
| untertitel | 10 / 10 |

| Prüfung | OK | Punkte | Detail |
|---|---|---|---|
| Auflösung 1080x1920 (9:16) | ✅ | 5/5 | 1080x1920 |
| 30 fps | ✅ | 2/2 | 30.00 |
| Dauer 30-60 s | ❌ | 0/4 | 81.0 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 9.5 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.2 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.4 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.2 LUFS |
| Sprachverständlichkeit (Whisper-Abgleich) | ✅ | 17.99/20 | Ø 0.87, 0 Zeile(n) < 0,75 |
| Keine Render-Fehler | ✅ | 5/5 | 0 fehlerhafte Bilder |
| Keine ungeplanten Schwarzbilder | ✅ | 4/4 | [] |
| Keine eingefrorenen Bilder > 2,5 s | ✅ | 4/4 | [] |
| Bildinhalt vorhanden (kein Leerbild) | ✅ | 2/2 | 0 leere Stichproben |
| Alle Figuren in der Datenbank | ✅ | 4/4 | [] |
| Aussehen = gesperrtes Model-Sheet | ✅ | 6/6 | abweichend: [], nicht gesperrt: [] |
| Hook in der 1. Sekunde | ✅ | 3/3 | 0.00 s |
| Cliffhanger + A/B-Abstimmung | ✅ | 4/4 |  |
| Zeilen ≤ 22 Wörter | ✅ | 2/2 | [] |
| Sprechtempo ≤ 4 Wörter/s | ✅ | 2/2 | [] |
| Einstellungslänge 1-8,5 s (Tempo) | ❌ | 0/2 | [0] |
| Nur Figuren aus dem Serien-Cast | ✅ | 2/2 | [] |
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 3 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Drei Uhr nachts. Und jemand klopft an meine Tür. | 3 Uhr in Harz und jemand klopft an meine Tür. | 0.78 |
| 1.0 | du | Was soll ich tun? A: Tür öffnen. Oder B: nicht öffnen? Schreib es in die Kommentare! | Was soll ich tun? A. Tür öffnen. Oder B. Nicht öffnen. Schreibt es in die Kommentare. | 0.96 |
