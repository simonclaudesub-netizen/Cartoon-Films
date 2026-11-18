# QC-Bericht – Versuch 3

**Gesamt: 94.0 / 100** – NICHT BESTANDEN (Mindestwert 90)

**Muss korrigiert werden (blockiert Veröffentlichung):**
- Zeile 3.0 (du): gehört 'Lina, die wohnt 300 km weit weg.'
- Zeile 5.0 (lina): gehört 'Ich bin...'

| Kategorie | Punkte |
|---|---|
| technik | 15 / 15 |
| ton | 15 / 15 |
| stimmen | 14.0 / 20 |
| bild | 15 / 15 |
| konsistenz | 10 / 10 |
| story | 15 / 15 |
| untertitel | 10 / 10 |

| Prüfung | OK | Punkte | Detail |
|---|---|---|---|
| Auflösung 1080x1920 (9:16) | ✅ | 5/5 | 1080x1920 |
| 30 fps | ✅ | 2/2 | 30.00 |
| Dauer 30-60 s | ✅ | 4/4 | 33.2 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 4.5 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.3 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.2 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.3 LUFS |
| Sprachverständlichkeit (Whisper-Abgleich) | ❌ | 14.0/20 | Ø 0.92, 2 Zeile(n) unter Mindestwert (0.85, lange Sätze strenger) oder mit Nachlaut/Wiederholung |
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
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 14 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Drei Uhr sieben. Diesmal schaue ich nach. | 3.07 Uhr. Diesmal schaue ich nach. | 0.883 |
| 1.0 | du | Leer. Nur Frau Brandts Hausschuhe. Ordentlich nebeneinander. | Lea, nur Frau Brandts Hausschuhe, ordentlich nebeneinander. | 0.904 |
| 2.0 | du | Moment. Da klopft jemand. Von innen. Bei Frau Brandt. | Moment, da klopft jemand von innen bei Frau Brandt. | 1.0 |
| 3.0 | du | Lina? Die wohnt dreihundert Kilometer weit weg. | Lina, die wohnt 300 km weit weg. | 0.717 |
| 4.0 | du | Da ist niemand. | Da ist niemand. | 1.0 |
| 5.0 | lina | Ich bin's. | Ich bin... | 0.83 |
| 5.1 | du | Lina hat noch nie gesagt: Ich bin's. | Lina hat noch nie gesagt, ich bin's. | 1.0 |
| 6.0 | du | Was soll ich tun? A: Lina anrufen. Oder B: Okan wecken? Schreib es in die Kommentare! | Was soll ich tun? a. Lina anrufen oder b. Okan wecken? Schreib es in die Kommentare | 1.0 |
