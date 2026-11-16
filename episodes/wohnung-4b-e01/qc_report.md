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
| Dauer 30-60 s | ✅ | 4/4 | 56.2 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 10.0 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.5 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.2 dBTP |
| Keine Übersteuerung | ✅ | 2/2 | 0.000 % Samples |
| Ton hörbar (nicht stumm) | ✅ | 3/3 | -14.5 LUFS |
| Sprachverständlichkeit (Whisper-Abgleich) | ✅ | 20.0/20 | Ø 0.97, 0 Zeile(n) unter 0.85 oder mit Nachlaut |
| Keine Render-Fehler | ✅ | 5/5 | 0 fehlerhafte Bilder |
| Keine ungeplanten Schwarzbilder | ✅ | 4/4 | [] |
| Keine eingefrorenen Bilder > 2,5 s | ✅ | 4/4 | [] |
| Bildinhalt vorhanden (kein Leerbild) | ✅ | 2/2 | 0 leere Stichproben |
| Alle Figuren in der Datenbank | ✅ | 4/4 | [] |
| Aussehen = gesperrtes Model-Sheet | ✅ | 6/6 | abweichend: [], nicht gesperrt: [] |
| Hook in der 1. Sekunde | ✅ | 3/3 | 0.00 s |
| Cliffhanger + A/B-Abstimmung | ✅ | 4/4 |  |
| Zeilen ≤ 22 Wörter | ✅ | 2/2 | [] |
| Sprechtempo ≤ 4 Wörter/s | ❌ | 0/2 | ['... dann bin das nicht ich.', 'Ich weiß, dass Sie da sind.'] |
| Einstellungslänge 1-8,5 s (Tempo) | ✅ | 2/2 | [] |
| Nur Figuren aus dem Serien-Cast | ✅ | 2/2 | [] |
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 25 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Drei Uhr nachts. Und jemand klopft an meine Tür. | 3 Uhr nachts und jemand klopft an meine Tür. | 1.0 |
| 1.0 | okan | Willkommen in 4B! Hier sind Ihre Schlüssel. | Sie kommen in 4B, hier sind Ihre Schlüssel. | 0.851 |
| 2.0 | okan | Es gibt nur eine Regel: Nach Mitternacht öffnen Sie niemandem die Tür. | Es gibt nur eine Regel, nach Mitternacht öffnen sie niemandem die Tür. | 1.0 |
| 2.1 | okan | Niemandem. | Niemandem. | 1.0 |
| 3.0 | du | Äh... und warum? | Und warum? | 1.0 |
| 3.1 | okan | Fragen Sie lieber nicht. | Fragen Sie lieber nicht. | 1.0 |
| 4.0 | helga | Ach, der Neue aus 4B! Ich bin Frau Brandt. Ich hab Ihnen Kuchen gebacken. | Ach, der Neue aus Vierbe, ich bin Frau Brandt. Ich habe Ihnen Kuchen gebacken. | 0.895 |
| 5.0 | helga | Und noch etwas. Wenn nachts jemand klopft und sagt: Ich bin's ... | und noch etwas, wenn nachts jemand klopft und sagt, ich bin's. | 1.0 |
| 6.0 | helga | ... dann bin das nicht ich. | Und dann bin das nicht ich. | 0.912 |
| 7.0 | du | Lina hält das für einen Witz. Ich nicht. | Lina hält das für einen Witz, ich nicht. | 1.0 |
| 8.0 | helga | Hallo? Ich bin's, Frau Brandt! Bitte machen Sie auf! | Hallo, ich bin es Frau Brandt, bitte machen Sie auf. | 0.936 |
| 9.0 | du | Aber sie hat gesagt ... das ist nicht sie. | Aber sie hat gesagt, das ist nicht sie. | 1.0 |
| 10.0 | helga | Ich weiß, dass Sie da sind. | Ich weiß, dass sie da sind. | 1.0 |
| 11.0 | du | Was soll ich tun? A: Tür öffnen. Oder B: nicht öffnen? Schreib es in die Kommentare! | Was soll ich tun? a. Triö öffnen oder b. Nicht öffnen? Schreib es in die Kommentare. | 0.955 |
