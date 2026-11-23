# QC-Bericht – Versuch 1

**Gesamt: 98.0 / 100** – BESTANDEN (Mindestwert 90)

| Kategorie | Punkte |
|---|---|
| technik | 15 / 15 |
| ton | 15 / 15 |
| stimmen | 20.0 / 20 |
| bild | 15 / 15 |
| konsistenz | 10 / 10 |
| story | 13 / 15 |
| untertitel | 10 / 10 |

| Prüfung | OK | Punkte | Detail |
|---|---|---|---|
| Auflösung 1080x1920 (9:16) | ✅ | 5/5 | 1080x1920 |
| 30 fps | ✅ | 2/2 | 30.00 |
| Dauer 30-60 s | ✅ | 4/4 | 44.4 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 7.4 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.2 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.3 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.2 LUFS |
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
| Sprechtempo ≤ 4 Wörter/s | ❌ | 0/2 | ['Das hat er nur einmal gesagt.'] |
| Einstellungslänge 1-8,5 s (Tempo) | ✅ | 2/2 | [] |
| Nur Figuren aus dem Serien-Cast | ✅ | 2/2 | [] |
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 24 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Vor meiner Tür spricht jemand mit meiner Stimme. Ich klopfe an die Wand zu meiner Nachbarin. | Vor meiner Tür spricht jemand mit meiner Stimme. Ich klopfe an die Wand zu meiner Nachbarin. | 1.0 |
| 1.0 | helga | Ich bin wach. Ich bin wach. | Ich bin wach. Ich bin wach. | 1.0 |
| 1.1 | du | Frau Brandt. Sie sagt es zweimal. Wie Okan. | Frau Brandt. Sie sagt es zweimal wie Okan. | 1.0 |
| 2.0 | helga | Mach nicht auf, Kind. Er war schon einmal hier. Lange vor dir. | Mach nicht auf, Kind. Er war schon einmal hier, lange vor dir. | 1.0 |
| 3.0 | du | Am Morgen lag ein altes Foto unter meiner Tür. | Am Morgen lag ein altes Foto unter meiner Tür. | 1.0 |
| 4.0 | du | Ein junger Mann. Vor meiner Tür. Vor Wohnung vier B. | Ein junger Mann, vor meiner Tür, vor Wohnung 4B. | 0.901 |
| 5.0 | du | Auf der Rückseite. Nicht öffnen. Nicht öffnen. Und ein O. | auf der Rückseite, nicht öffnen, nicht öffnen und ein O. | 1.0 |
| 5.1 | du | Das ist nicht Okans Schrift. | Das ist nicht Okanz Schrift. | 0.865 |
| 6.0 | okan | Wirf das Foto weg. | Wirf das Foto weg. | 1.0 |
| 6.1 | du | Das hat er nur einmal gesagt. | Das hat er nur einmal gesagt. | 1.0 |
| 7.0 | du | Was soll ich tun? A: Foto behalten. Oder B: Foto wegwerfen? Schreib es in die Kommentare! | Was soll ich tun? A. Foto behalten. Oder B. Foto wegwerfen. Schreib es in die Kommentare. | 1.0 |
