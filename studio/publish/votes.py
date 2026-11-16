"""Zuschauer-Abstimmungen aus Kommentaren auswerten (A/B).

YouTube: automatisch über commentThreads.list.
TikTok:  keine offizielle Kommentar-Schnittstelle für normale Entwickler ->
         Kommentare als Textdatei importieren (eine Zeile pro Kommentar) oder
         Zählwerte direkt eintragen.
Jede Person zählt einmal (letzte eindeutige Stimme gilt).
"""
import re

PATTERNS = {
    "A": [r"^\W*a\W*$", r"\b(antwort|option|team|für)\s*a\b", r"^\W*a[\s!.,]", r"\btür (auf|öffnen)\b", r"\bmach auf\b", r"[\s,.!:]a\W*$"],
    "B": [r"^\W*b\W*$", r"\b(antwort|option|team|für)\s*b\b", r"^\W*b[\s!.,]", r"\bnicht öffnen\b", r"\bbleib drin\b",
          r"\bniemals\b", r"[\s,.!:]b\W*$"],
}


def classify(text, options=None):
    t = text.strip().lower()
    hits = set()
    for k, pats in PATTERNS.items():
        if any(re.search(p, t) for p in pats):
            hits.add(k)
    for k, label in (options or {}).items():
        if label and label.lower() in t:
            hits.add(k)
    if "nicht öffnen" in t:
        hits.discard("A")
    return hits.pop() if len(hits) == 1 else None


def tally(comments, options=None):
    by_author = {}
    for i, c in enumerate(comments):
        v = classify(c["text"], options)
        if v:
            by_author[c.get("author") or f"anon{i}"] = v
    counts = {"A": 0, "B": 0}
    for v in by_author.values():
        counts[v] += 1
    total = counts["A"] + counts["B"]
    winner = None if total == 0 or counts["A"] == counts["B"] else max(counts, key=counts.get)
    return {"counts": counts, "total": total, "winner": winner}


def merge(*tallies):
    c = {"A": 0, "B": 0}
    for t in tallies:
        for k in c:
            c[k] += t["counts"][k]
    total = c["A"] + c["B"]
    return {"counts": c, "total": total,
            "winner": None if total == 0 or c["A"] == c["B"] else max(c, key=c.get)}
