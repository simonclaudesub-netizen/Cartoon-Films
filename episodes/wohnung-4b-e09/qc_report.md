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
| Dauer 30-60 s | ✅ | 4/4 | 41.8 s |
| H.264/yuv420p + AAC | ✅ | 2/2 | h264/yuv420p |
| Dateigröße < 250 MB | ✅ | 2/2 | 7.3 MB |
| Lautheit -14 LUFS ±1,5 | ✅ | 6/6 | -14.1 LUFS |
| True Peak ≤ -1 dBTP | ✅ | 4/4 | -1.2 dBTP |
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
| Jede Dialogzeile untertitelt | ✅ | 4/4 | 22 Einblendungen |
| Max. 30 Zeichen je Einblendung | ✅ | 2/2 | [] |
| Mindest-Lesezeit 0,4 s | ✅ | 2/2 | [] |
| Keine Überlappung, innerhalb der Laufzeit | ✅ | 2/2 |  |

## Sprachtest (Whisper hört jede Zeile ab)

| Zeile | Sprecher | Soll | Gehört | Ähnlichkeit |
|---|---|---|---|---|
| 0.0 | du | Ich habe dieses Foto gestern weggeworfen. Heute Morgen lag es wieder unter meiner Tür. | Ich habe dieses Foto gestern weggeworfen. Heute Morgen lag es wieder unter meiner Tür. | 1.0 |
| 1.0 | du | Unten im Hof. In die Mülltonne. Ich weiß es genau. | im Hof, in die Mülltonne, ich weiß es genau. | 0.941 |
| 2.0 | du | Aber jetzt ist da noch jemand. Neben dem jungen Mann. | Aber jetzt ist da noch jemand, neben dem jungen Mann. | 1.0 |
| 3.0 | du | Die Person trägt meinen gelben Pullover. | die Person trägt meinen gelben Pullover. | 1.0 |
| 4.0 | du | Und auf der Rückseite steht jetzt: Nicht wegwerfen. Nicht wegwerfen. | Und auf der Rückseite steht jetzt nicht wegwerfen, nicht wegwerfen. | 1.0 |
| 5.0 | helga | Das Foto kommt immer zurück, Kind. Bei Oskar war es genauso. | Das Foto kommt immer zurück, Kind. Bei Oscar war es genauso. | 0.938 |
| 5.1 | du | Oskar. Der Vormieter von Wohnung vier B. | Oskar, der Vormieter von Wohnung 4B | 0.856 |
| 6.0 | du | Wer hat es dann heute Nacht unter meine Tür geschoben? | Wer hat es dann heute Nacht unter meine Tür geschoben? | 1.0 |
| 7.0 | du | Was soll ich tun? A: Frau Brandt ausfragen. Oder B: Okan das Foto zeigen? Schreib es in die Kommentare! | Was soll ich tun? A. Frau Brandt ausfragen. Oder B. Okaan das Foto zeigen? Schreib es in die Kommentare. | 0.966 |
