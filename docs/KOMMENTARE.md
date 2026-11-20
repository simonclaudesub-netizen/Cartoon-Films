# YouTube-Kommentare beantworten

Freigabe des Kanalinhabers (19.11.2026): Claude antwortet öffentlich im Namen des Kanals „Du entscheidest“.
TikTok: keine Schnittstelle für Antworten – nur in der App durch den Menschen.

## Ablauf (Teil jeder Dashboard-Aktualisierung, siehe docs/DASHBOARD.md)
1. `python3 -m studio.publish.comments abstimmung` – setzt unter die neueste öffentliche Folge einmal den
   Abstimmungs-Kommentar („Was soll ich tun? 🅰️ … oder 🅱️ …?“). Anpinnen geht per API nicht.
2. `python3 -m studio.publish.comments offen` → `stats/kommentare_offen.json` lesen.
3. Antworten schreiben (Regeln unten) nach `stats/antworten.json` als `[{"id": "<Kommentar-ID>", "text": "…"}]`.
   Kommentare, auf die nicht geantwortet wird, einfach weglassen.
4. `python3 -m studio.publish.comments antworten stats/antworten.json` – sendet höchstens 20, prüft Länge,
   Links und Doppelte; antwortet nur auf noch offene Kommentare (ein Kommentar nie zweimal).
5. Im Bericht nur die Zahl nennen („3 Antworten, 1 übersprungen“). Nichts committen.

## Regeln für die Antworten
- **Stimme:** der Ich-Erzähler aus der Serie („ich“ = die Hauptfigur in Wohnung 4B), locker, kurz,
  1–2 Sätze, Deutsch (bzw. in der Sprache des Kommentars). Höchstens 1–2 Emojis.
- **Jede Antwort anders.** Keine Textbausteine, keine Wiederholungen über Kommentare hinweg.
- **Auf den Inhalt eingehen:** Stimme (A/B) aufgreifen („B ist notiert – ich hoffe, du hast recht 😬“),
  Theorien neugierig kommentieren, ohne sie zu bestätigen oder zu widerlegen.
- **Keine Spoiler:** nichts aus kommenden Folgen, aus `next_plans` oder `staffel_bogen` verraten.
- **Abstimmung nicht verfälschen:** keine eigene Empfehlung für A oder B, keine Stimmen „zählen lassen“,
  die keine sind (z. B. „C“ freundlich ablehnen).
- **Ehrlich:** Fragt jemand, ob das KI ist: ja – die Serie wird mit KI animiert und vertont.
  Keine Versprechen (Uhrzeiten außer „jeden Tag 18 Uhr“, Gewinnspiele, Treffen).
- **Nicht antworten** auf Spam, Werbung, Links, Beleidigungen, Hass, sexuelle Inhalte, persönliche
  Daten oder Kommentare, die offensichtlich von Kindern Persönliches preisgeben – einfach überspringen.
- Keine Links, keine @-Erwähnungen, keine Bitten um Abos/Likes in jeder Antwort (höchstens selten).
- **Ideen/Wünsche** („C: …“, „beides“, Vorschläge): freundlich aufgreifen, z. B. „Notiert! 📝“ – ohne zu
  versprechen, dass oder wann es vorkommt. Sie werden beim nächsten Drehbuch gelesen (AUTOPILOT Schritt 3b).
- Kritik sachlich und freundlich annehmen („Danke, nehme ich mit!“), nie streiten.
