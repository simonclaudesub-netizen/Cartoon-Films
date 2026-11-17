# QC-Bericht – Versuch 1

**Gesamt: 99.0 / 100** – BESTANDEN (Mindestwert 90)

| Kategorie | Punkte |
|---|---|
| technik | 15 / 15 |
| ton | 15 / 15 |
| stimmen | 20.0 / 20 |
| bild | 15 / 15 |
| konsistenz | 10 / 10 |
| story | 15 / 15 |
| untertitel | 9 / 10 |

| Prüfung | OK | Punkte | Detail |
|---|---|---|---|
| Auflösung 1080x1920 (9:16) | ✅ | 5/5 | 1080x1920 |
| 30 fps | ✅ | 2/2 | 30.00 |
| Dauer 30-60 s | ✅ | 4/4 | 52.3 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 9.4 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.3 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.2 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.3 LUFS |
| Sprachverständlichkeit (Whisper-Abgleich) | ✅ | 20.0/20 | Ø 0.98, 0 Zeile(n) unter Mindestwert (0.85, lange Sätze strenger) oder mit Nachlaut/Wiederholung |
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
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 26 Einblendungen |
| Max. 36 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ❌ | 1/2 | ['Ja.'] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Ihr habt euch für B entschieden. Richtige Antwort ... oder? | Ihr habt Euch für B entschieden. Richtige Antwort oder? | 1.0 |
| 1.0 | du | Nach dreißig Minuten ununterbrochenem Klopfen ging sie endlich. | Nach 30 Minuten ununterbrochenem Klopfen ging sie endlich. | 0.895 |
| 2.0 | du | Doch schlafen konnte ich diese Nacht nicht. | Doch schlafen konnte ich diese Nacht nicht. | 1.0 |
| 3.0 | du | Ich beschloss herauszufinden, was hier los ist. | Ich beschloss herauszufinden, was hier los ist. | 1.0 |
| 4.0 | du | Am Morgen lag ein Zettel unter meiner Tür. | Am Morgen lag ein Zettel unter meiner Tür. | 1.0 |
| 5.0 | du | Guten Morgen, Frau Brandt. Haben Sie heute Nacht bei mir geklopft? | Guten Morgen Frau Brandt, haben Sie heute Nacht bei mir geklopft? | 1.0 |
| 5.1 | helga | Ich? Ich habe die ganze Nacht geschlafen. Wie ein Stein! | ich? Ich habe die ganze Nacht geschlafen, wie ein Stein. | 1.0 |
| 6.0 | helga | Aber ... hat die Stimme gesagt: Ich bin's? | Aber, hat die Stimme gesagt, ich bin's. | 1.0 |
| 6.1 | du | Ja. | Ja. | 1.0 |
| 7.0 | helga | Dann sind Sie nicht der Erste. | Und dann sind sie nicht der Erste. | 0.928 |
| 8.0 | okan | Frau Brandt. Wir reden nicht über den Vormieter. | Frau Brandt, wir reden nicht über den Vormieter. | 1.0 |
| 8.1 | okan | Nicht über den Vormieter. | Nicht über den Vormieter. | 1.0 |
| 9.0 | du | Was soll ich tun? A: Heute Nacht durch den Türspion schauen. Oder B: Okan heimlich folgen? Schreib es in die Kommentare! | Was soll ich tun? A. Heute Nacht durch den Türspion schauen oder B. O kann heimlich folgen? Schreib es in die Kommentare. | 0.955 |
