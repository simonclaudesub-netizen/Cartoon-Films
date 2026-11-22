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
| Dauer 30-60 s | ✅ | 4/4 | 34.8 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 5.3 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.2 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.3 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.2 LUFS |
| Sprachverständlichkeit (Whisper-Abgleich) | ✅ | 20.0/20 | Ø 0.97, 0 Zeile(n) unter Mindestwert (0.85, lange Sätze strenger) oder mit Nachlaut/Wiederholung |
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
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 16 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Vor meiner Tür steht der Hausmeister. Aber der echte ist noch unten. | Vor meiner Tür steht der Hausmeister, aber der Echte ist noch unten. | 1.0 |
| 1.0 | du | Okan. Wie hieß der Vormieter von Wohnung 4B? | Wie hieß der Vormieter von Wohnung 4B? | 0.935 |
| 2.0 | du | Wie hieß der Vormieter von Wohnung 4B? | Wie hieß der Vormieter von Wohnung 4B? | 1.0 |
| 2.1 | du | Das ist meine Stimme. | Das ist meine Stimme. | 1.0 |
| 3.0 | okan | Jetzt kennt er auch deine Stimme. Deine Stimme. | Jetzt kennt er auch deine Stimme. Deine Stimme. | 1.0 |
| 4.0 | du | Er hat Lina gehört. Okan. Und jetzt mich. | Er hat Lina gehört. Oh, kann. Und jetzt mich. | 0.879 |
| 5.0 | du | Mach auf. Ich bin's. | Mach auf. Ich bin's. | 1.0 |
| 5.1 | du | Aber ich stehe doch hier drinnen. | Aber ich stehe doch hier drinnen. | 1.0 |
| 6.0 | du | Was soll ich tun? A: Okan hochholen. Oder B: Frau Brandt fragen? Schreib es in die Kommentare! | Was soll ich tun? A. Wo kann hochholen? Oder B. Frau Brandt fragen? Schreib es in die Kommentare. | 0.942 |
