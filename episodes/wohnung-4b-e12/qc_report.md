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
| Dauer 30-60 s | ✅ | 4/4 | 35.7 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 6.4 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.1 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.2 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.1 LUFS |
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
| Sprechtempo ≤ 4 Wörter/s | ❌ | 0/2 | ['Hinter mir fällt die Tür zu.'] |
| Einstellungslänge 1-8,5 s (Tempo) | ✅ | 2/2 | [] |
| Nur Figuren aus dem Serien-Cast | ✅ | 2/2 | [] |
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 18 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Jemand hat mich aus meiner abgeschlossenen Wohnung angerufen. Also schließe ich auf. | Jemand hat mich aus meiner abgeschlossenen Wohnung angerufen, also schließe ich auf. | 1.0 |
| 1.0 | du | Leer. Niemand da. | leer. Niemand da. | 1.0 |
| 2.0 | du | Danke, dass du aufgeschlossen hast. | Danke, dass du aufgeschlossen hast. | 1.0 |
| 2.1 | du | Das kam aus meinem Schlafzimmer. Mit meiner Stimme. | Das kam aus meinem Schlafzimmer mit meiner Stimme. | 1.0 |
| 3.0 | du | Im Flur liegt ein neues Foto. | im Flur liegt ein neues Foto. | 1.0 |
| 4.0 | du | Das bin ich. Vor meiner Tür. Gerade eben, als ich aufgeschlossen habe. | Das bin ich vor meiner Tür, gerade eben als ich aufgeschlossen habe. | 1.0 |
| 5.0 | okan | Komm sofort raus. Komm sofort raus. | Komm sofort raus, komm sofort raus! | 1.0 |
| 5.1 | du | Hinter mir fällt die Tür zu. | Hinter mir fällt die Tür zu. | 1.0 |
| 6.0 | du | Was soll ich tun? A: Durchs Fenster um Hilfe rufen. Oder B: Ins Schlafzimmer schauen? Schreib es in die Kommentare! | Was soll ich tun? A. Durchs Fenster um Hilfe rufen oder B. ins Schlafzimmer schauen. Schreib es in die Kommentare. | 1.0 |
