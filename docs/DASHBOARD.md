# Kanal-Übersicht (Dashboard) aktualisieren

Seite: https://claude.ai/artifact/2kYZpzpZNWnx7a5XbqDAts (Artifact-Typ „Data“).
Die Seite kann YouTube/TikTok nicht selbst abfragen (kein Connector), daher lädt eine geplante Aufgabe
etwa alle 3 Stunden neue Zahlen hoch.

1. `git pull -q origin main` und `python3 -m studio.stats` → schreibt `stats/videos.json`, `stats/kanaele.json`,
   `stats/abstimmungen.json` (nur lesende Abfragen: YouTube Data API, Buffer-API).
2. Jede der drei Dateien mit dem Artifact-Werkzeug als Asset hochladen
   (`url` = Seite oben, `asset: true`, `file_path` = Datei) → neue `/_blob/<id>`-Adresse.
3. Mit ArtifactData die Datensätze `datasets/videos`, `datasets/kanaele`, `datasets/abstimmungen` per `update`
   ändern: `source.url` = neue Adresse, `updated` = `{"at": <jetzt UTC ISO>, "by": "Claude (studio/stats.py)"}`
   (vorher `get`, um `if_version` und die alte Adresse zu kennen).
4. Die alten Assets löschen (Artifact `action: "delete"`, `url` = Seite, `path` = alte Asset-ID, die 32 Zeichen
   nach `/_blob/`), damit sich nichts ansammelt.
5. **YouTube-Kommentare beantworten** nach `docs/KOMMENTARE.md` (Abstimmungs-Kommentar, offene Kommentare,
   höchstens 20 Antworten pro Lauf).
6. Nichts committen, keine Nachricht ans Handy. Bei Fehlern nur kurz im Bericht nennen.
