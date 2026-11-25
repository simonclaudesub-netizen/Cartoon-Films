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
| Dauer 30-60 s | ✅ | 4/4 | 36.0 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 6.9 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.1 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.4 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.1 LUFS |
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
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 18 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Der Mann auf dem Foto vor meiner Tür ist seit über vierzig Jahren verschwunden. | Der Mann auf dem Foto vor meiner Tür ist seit über 40 Jahren verschwunden. | 1.0 |
| 1.0 | helga | Oskar. Er hat früher in deiner Wohnung gewohnt. | Und Oscar, er hat früher in deiner Wohnung gewohnt. | 0.869 |
| 2.0 | helga | Mitten in der Nacht hat es bei ihm geklopft. Mit seiner eigenen Stimme. | mitten in der Nacht, hat es bei ihm geklopft, mit seiner eigenen Stimme. | 1.0 |
| 3.0 | helga | Er hat aufgemacht. Am Morgen war nur noch das Foto da. | der hat aufgemacht. Am Morgen war nur noch das Foto da. | 0.942 |
| 4.0 | du | Und seitdem kommt das Foto zu jedem, der in meiner Wohnung wohnt? | Seitdem kommt das Foto zu jedem, der in meiner Wohnung wohnt. | 0.961 |
| 4.1 | helga | Zu jedem. Zu jedem. | Zu jedem, zu jedem. | 1.0 |
| 5.0 | helga | Hallo. Ich bin es. | Hallo, ich bin es. | 1.0 |
| 5.1 | du | Das ist ihre eigene Stimme. | Das ist ihre eigene Stimme. | 1.0 |
| 6.0 | du | Was soll ich tun? A: Sofort auflegen. Oder B: Weiter zuhören? Schreib es in die Kommentare! | Was soll ich tun? A. sofort auflegen oder B. weiterzuhören? Schreib es in die Kommentare. | 0.94 |
