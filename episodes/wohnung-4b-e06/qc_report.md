# QC-Bericht – Versuch 1

**Gesamt: 100.0 / 100** – BESTANDEN (Mindestwert 90)

| Kategorie | Punkte |
|---|---|
| technik | 15 / 15 |
| ton | 15 / 15 |
| stimmen | 20.0 / 20 |
| bild | 15 / 15 |
| konsistenz | 10 / 10 |
| story | 15 / 15 |
| untertitel | 10 / 10 |

| Prüfung | OK | Punkte | Detail |
|---|---|---|---|
| Auflösung 1080x1920 (9:16) | ✅ | 5/5 | 1080x1920 |
| 30 fps | ✅ | 2/2 | 30.00 |
| Dauer 30-60 s | ✅ | 4/4 | 36.5 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 5.5 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.3 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.4 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.3 LUFS |
| Sprachverständlichkeit (Whisper-Abgleich) | ✅ | 20.0/20 | Ø 1.00, 0 Zeile(n) unter Mindestwert (0.85, lange Sätze strenger) oder mit Nachlaut/Wiederholung |
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
| Einstellungslänge 1-8,5 s (Tempo) | ✅ | 2/2 | [] |
| Nur Figuren aus dem Serien-Cast | ✅ | 2/2 | [] |
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 19 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Der Hausmeister steht vor meiner Tür. Und ruft mich gleichzeitig an. | Der Hausmeister steht vor meiner Tür und ruft mich gleichzeitig an. | 1.0 |
| 1.0 | okan | Ich bin noch unten. Ich bin noch unten. | Ich bin noch unten, ich bin noch unten. | 1.0 |
| 1.1 | du | Zweimal. | zweimal. | 1.0 |
| 2.0 | du | Er lächelt. Okan lächelt nie. | Er lächelt. Okan lächelt nie. | 1.0 |
| 3.0 | okan | Okan hier. Okan hier. | Okan hier, Okan hier. | 1.0 |
| 3.1 | du | Genau das hat er vorhin gesagt. Wort für Wort. | Genau das hat er vorhin gesagt. Wort für Wort. | 1.0 |
| 4.0 | okan | Hör zu. Er hat mich vorhin zweimal gehört. | Hör zu, er hat mich vorhin zweimal gehört. | 1.0 |
| 4.1 | du | Dann kann er es auch zweimal sagen. | Dann kann er es auch zweimal sagen. | 1.0 |
| 5.0 | du | Einer von beiden ist nicht Okan. | Einer von beiden ist nicht Okan. | 1.0 |
| 6.0 | du | Wer ist der echte Okan? A: Okan vor der Tür. Oder B: Okan am Telefon? Schreib es in die Kommentare! | Wer ist der echte Okan A. Okan vor der Tür oder B. Okan am Telefon? Schreib es in die Kommentare. | 1.0 |
