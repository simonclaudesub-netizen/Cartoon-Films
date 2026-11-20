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
| Dauer 30-60 s | ✅ | 4/4 | 50.6 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 7.3 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.5 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.3 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.5 LUFS |
| Sprachverständlichkeit (Whisper-Abgleich) | ✅ | 20.0/20 | Ø 0.99, 0 Zeile(n) unter Mindestwert (0.85, lange Sätze strenger) oder mit Nachlaut/Wiederholung |
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
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 25 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Vor meiner Tür steht jemand, der jede Stimme nachmachen kann. | Vor meiner Tür steht jemand, der jede Stimme nachmachen kann. | 1.0 |
| 1.0 | du | Ich rufe den Hausmeister an. Okan. | Ich rufe den Hausmeister an. | 0.912 |
| 1.1 | okan | Ich komme hoch. Mach nicht auf. Mach nicht auf. | Ich komme hoch. Mach nicht auf. Mach nicht auf. | 1.0 |
| 2.0 | du | Frau Brandt auch wecken? Nein. Bei ihr hat es von innen geklopft. | Frau Brandt auch wecken. Nein, bei ihr hat es von innen geklopft. | 1.0 |
| 3.0 | okan | Okan hier. Okan hier. | Okan hier, Okan hier. | 1.0 |
| 3.1 | du | Er sagt alles zweimal. | Er sagt alles zweimal. | 1.0 |
| 4.0 | okan | Hör zu. Was er hört, kann er sagen. Aber nur einmal. Nur einmal. | hört zu. Was er hört, kann er sagen, aber nur einmal, nur einmal. | 0.95 |
| 5.0 | okan | Er hat Lina gehört. Und jetzt hört er mich. | Er hat Lina gehört, und jetzt hört er mich. | 1.0 |
| 5.1 | du | Also sagt der echte Okan alles zweimal. | Also sagt der echte Okan alles zweimal. | 1.0 |
| 6.0 | okan | Gut. Jetzt kannst du aufmachen. | Gut, jetzt kannst du aufmachen. | 1.0 |
| 6.1 | du | Das hat er nur einmal gesagt. | Das hat er nur einmal gesagt. | 1.0 |
| 7.0 | du | Was soll ich tun? A: Durch den Türspion schauen. Oder B: Okan zurückrufen? Schreib es in die Kommentare! | Was soll ich tun? A. Durch den Türspion schauen oder B. Okan zurückrufen? Schreib es in die Kommentare. | 1.0 |
