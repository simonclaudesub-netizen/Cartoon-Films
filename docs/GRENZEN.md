# Ehrliche Grenzen (Stand 16.11.2026)

## Was technisch NICHT geht oder eingeschränkt ist

1. **Kein KI-Bildgenerator.** Ohne GPU und ohne externe Dienste gibt es keine Diffusions-Modelle.
   Bilder entstehen stattdessen mit einer eigenen Vektor-Zeichen-Engine. Vorteil: Figuren sind
   garantiert identisch. Nachteil: Neue Kulissen, Requisiten oder Posen müssen als Code ergänzt
   werden (das kann Claude in der täglichen Sitzung tun), und der Detailgrad ist etwas einfacher als
   bei handgezeichneten oder KI-generierten Bildern.
2. **Animation ist „Limited Animation“.** Mundbewegung aus der Lautstärke (nicht phonemgenau),
   Blinzeln, Kopfnicken, Gesten, Laufen ins Bild, Kamerafahrten, Licht-Effekte. Komplexe
   Körperbewegungen (Rennen, Kämpfen, Hinsetzen) sind nicht vorhanden.
3. **Stimmen.** Hauptstimmen kommen von Chatterbox Multilingual (lokal, MIT-Lizenz, Stimmklon
   aus 10-s-Referenzen). Sie klingen deutlich natürlicher als Piper, sind aber langsam auf der CPU
   (ca. 5-6x Echtzeit, ~5 Minuten pro Episode) und hängen gelegentlich Silben an – die Whisper-QC
   erkennt das und lässt die Zeile automatisch neu einsprechen („Take 2“). Echtes Flüstern kann das
   Modell nicht (wird mit Effekt simuliert). Referenzstimmen stammen nur aus frei lizenzierten
   Datensätzen (Thorsten CC0, HUI-Korpus/LibriVox gemeinfrei). Piper bleibt als Rückfallebene.
4. **Geschichten brauchen Claude.** Die lokale Software kann keine originellen Geschichten erfinden.
   Das Schreiben übernimmt Claude in einer täglich geplanten Sitzung. Ohne diese Sitzung
   produziert das Studio nichts Neues.
5. **TikTok – automatisches öffentliches Posten ist nicht regelkonform möglich** (geprüft 16.11.2026):
   - Die Content-Sharing-Richtlinien nennen ausdrücklich als nicht akzeptabel: „A utility tool to help
     upload contents to the account(s) you or your team manages“ – genau dieser Anwendungsfall.
   - Ungeprüfte Apps: nur SELF_ONLY-Posts, Konto muss privat sein, max. 5 Nutzer/24 h.
   - Jeder Post braucht eine Nutzeraktion (Vorschau, manuelle Sichtbarkeitswahl ohne Vorgabe, Zustimmung).
   - **Deshalb:** TikTok läuft halbautomatisch. Das Studio erzeugt Video + `tiktok_upload.txt`
     (Beschreibung, Checkliste); der Mensch lädt in der TikTok-App hoch (ca. 30 s).
   - Kommentare eigener Videos lassen sich nicht per offizieller API lesen → Kommentare in
     `episodes/<id>/tiktok_comments.txt` einfügen oder `python -m studio votes <id> --a N --b N`.
   - Der vorhandene API-Code (`studio/publish/tiktok.py`) bleibt für einen späteren, regelkonformen
     Einsatz erhalten, ist aber abgeschaltet.
6. **YouTube:**
   - Braucht ein Google-Cloud-Projekt mit aktivierter YouTube Data API v3, einen OAuth-Client und
     eine einmalige Zustimmung durch den Kanalinhaber.
   - Laut aktueller Doku kostet ein Upload 1 Einheit im eigenen „Video Uploads“-Kontingent
     (100 Aufrufe pro Tag); Kommentare lesen kostet 1 Einheit pro Aufruf.
7. **Dauerbetrieb:** Die Cloud-Umgebung ist flüchtig. Für den täglichen Betrieb liegt das Projekt in
   einem privaten Git-Repository; eine geplante Aufgabe startet täglich eine neue Sitzung, die
   `setup.sh` ausführt (ca. 10 Minuten Installation pro Tag, da nichts zwischengespeichert bleibt).
   Fertige Videos (`final.mp4`) werden nicht im Git gespeichert, nur auf YouTube.
8. **Rechtliches/Plattformregeln:** KI-Kennzeichnung ist eingebaut. Die Plattformregeln zu
   Massen-/Automatik-Inhalten und Monetarisierung entscheiden die Plattformen selbst.

## Was zuverlässig funktioniert (getestet)
- Komplette Produktion einer 30–60-s-Episode in ca. 3 Minuten auf 4 CPU-Kernen
- Automatische QC mit Punktwert, Korrekturschleife (max. 3), Sperre bei Nichtbestehen
- Nur geänderte Einstellungen werden bei Korrekturen neu gerendert (Shot-Cache)
- Upload-Code für YouTube/TikTok nach offizieller Doku (ohne echte Zugangsdaten nur als
  Trockenlauf `--dry-run` getestet)
