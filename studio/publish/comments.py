"""YouTube-Kommentare beantworten (öffentlich im Namen des Kanals; Freigabe Kanalinhaber 19.11.2026).

Die Antworten schreibt Claude (Regeln: docs/KOMMENTARE.md). Dieses Modul sammelt nur offene Kommentare
und schickt fertige Antworten ab – mit harten Grenzen, die unabhängig vom Text gelten:
  * höchstens MAX_PER_RUN Antworten pro Lauf, jeder Kommentar nur einmal (geprüft an YouTube selbst:
    hat der Thread schon eine Antwort des Kanals, wird er übersprungen),
  * keine Links, höchstens MAX_LEN Zeichen, keine zwei gleichen Antworten im selben Lauf.

  python -m studio.publish.comments offen            -> stats/kommentare_offen.json
  python -m studio.publish.comments antworten <datei> -> [{"id": <Kommentar-ID>, "text": "..."}]
  python -m studio.publish.comments abstimmung        -> Abstimmungs-Kommentar unter die neueste öffentliche Folge

API (YouTube Data API v3, Scope youtube.force-ssl, je Schreibvorgang 50 Kontingent-Einheiten):
  GET  commentThreads?part=snippet,replies&videoId=...      (offene Kommentare)
  POST comments?part=snippet  {"snippet": {"parentId", "textOriginal"}}            (Antwort)
  POST commentThreads?part=snippet {"snippet": {"videoId", "topLevelComment": ...}} (eigener Kommentar)
Anpinnen und Herzen gibt es in der API nicht.
"""
import json
import re
import sys

import requests

from .. import db
from . import youtube

API = "https://www.googleapis.com/youtube/v3"
MAX_PER_RUN = 20
MAX_LEN = 280
LINK = re.compile(r"https?://|www\.|\b[\w-]+\.(com|de|net|org|io|ly|me|gg)\b", re.I)
_CHANNEL = {}


def _h():
    return {"Authorization": f"Bearer {youtube._token()}"}


def channel_id():
    if "id" not in _CHANNEL:
        r = requests.get(f"{API}/channels", params={"part": "id", "mine": "true"}, headers=_h(), timeout=30)
        r.raise_for_status()
        _CHANNEL["id"] = r.json()["items"][0]["id"]
    return _CHANNEL["id"]


def _published():
    """[(episode_id, video_id, script)] aller hochgeladenen Folgen."""
    out = []
    for d in sorted((db.ROOT / "episodes").iterdir()):
        st, sc = d / "status.json", d / "script.json"
        if st.exists() and sc.exists():
            yt = (json.loads(st.read_text()).get("published") or {}).get("youtube")
            if yt:
                out.append((d.name, yt["id"], json.loads(sc.read_text())))
    return out


def _threads(video_id):
    out, page = [], None
    for _ in range(10):
        p = {"part": "snippet,replies", "videoId": video_id, "maxResults": 100, "textFormat": "plainText"}
        if page:
            p["pageToken"] = page
        r = requests.get(f"{API}/commentThreads", params=p, headers=_h(), timeout=30)
        if r.status_code == 403 and "commentsDisabled" in r.text:
            return []
        r.raise_for_status()
        j = r.json()
        out += j.get("items", [])
        page = j.get("nextPageToken")
        if not page:
            break
    return out


def _author(sn):
    return (sn.get("authorChannelId") or {}).get("value")


def open_comments():
    """Kommentare ohne Antwort des Kanals, mit dem Kontext, den Claude zum Antworten braucht
    (bewusst OHNE next_plans, damit nichts aus kommenden Folgen verraten wird)."""
    me = channel_id()
    out = []
    for ep, vid, sc in _published():
        for th in _threads(vid):
            top = th["snippet"]["topLevelComment"]
            sn = top["snippet"]
            if _author(sn) == me:
                continue
            replies = (th.get("replies") or {}).get("comments", [])
            if any(_author(c["snippet"]) == me for c in replies):
                continue
            out.append({"id": top["id"], "folge": sc.get("episode"), "episode_id": ep, "video": vid,
                        "titel": sc.get("title"), "inhalt": sc.get("summary"),
                        "abstimmung": (sc.get("cliffhanger") or {}).get("options"),
                        "autor": sn.get("authorDisplayName"), "text": sn.get("textOriginal", ""),
                        "likes": sn.get("likeCount", 0), "zeit": sn.get("publishedAt")})
    out.sort(key=lambda c: (-c["likes"], c["zeit"] or ""))
    return out


def check_text(text):
    """Fehlertext oder None. Harte Grenzen unabhängig davon, was Claude schreibt."""
    t = (text or "").strip()
    if not t:
        return "leer"
    if len(t) > MAX_LEN:
        return f"zu lang ({len(t)} > {MAX_LEN})"
    if LINK.search(t):
        return "enthält einen Link"
    if "@" in t:
        return "enthält @-Erwähnung"
    return None


def reply(parent_id, text):
    r = requests.post(f"{API}/comments", params={"part": "snippet"}, headers=_h(), timeout=30,
                      json={"snippet": {"parentId": parent_id, "textOriginal": text.strip()}})
    r.raise_for_status()
    return r.json()["id"]


def post_top(video_id, text):
    r = requests.post(f"{API}/commentThreads", params={"part": "snippet"}, headers=_h(), timeout=30,
                      json={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}})
    r.raise_for_status()
    return r.json()["id"]


def send(answers):
    """answers = [{"id", "text"}]. Antwortet nur auf aktuell offene Kommentare. -> (gesendet, übersprungen)"""
    open_ids = {c["id"] for c in open_comments()}
    sent, skipped, seen = [], [], set()
    for a in answers:
        cid, text = a.get("id"), (a.get("text") or "").strip()
        why = check_text(text)
        if not why and cid not in open_ids:
            why = "nicht (mehr) offen"
        if not why and text.lower() in seen:
            why = "gleiche Antwort doppelt"
        if not why and len(sent) >= MAX_PER_RUN:
            why = f"Grenze {MAX_PER_RUN} pro Lauf erreicht"
        if why:
            skipped.append({"id": cid, "grund": why})
            continue
        try:
            sent.append({"id": cid, "antwort_id": reply(cid, text), "text": text})
            seen.add(text.lower())
        except requests.HTTPError as e:
            skipped.append({"id": cid, "grund": f"YouTube: {e.response.status_code} {e.response.text[:120]}"})
    return sent, skipped


def vote_text(sc):
    o = (sc.get("cliffhanger") or {}).get("options") or {}
    n = (sc.get("episode") or 0) + 1
    return (f"Was soll ich tun? 🅰️ {o.get('A', 'A')} oder 🅱️ {o.get('B', 'B')}? "
            f"Schreib A oder B – die Mehrheit entscheidet Teil {n} 👀")


def vote_comments():
    """Eigener Abstimmungs-Kommentar unter die neueste öffentliche Folge, falls sie noch keinen hat."""
    me, done = channel_id(), []
    pubs = _published()
    if not pubs:
        return done
    r = requests.get(f"{API}/videos", params={"part": "status", "id": ",".join(v for _, v, _ in pubs)},
                     headers=_h(), timeout=30)
    r.raise_for_status()
    public = {it["id"] for it in r.json().get("items", []) if it["status"]["privacyStatus"] == "public"}
    live = [(ep, vid, sc) for ep, vid, sc in pubs if vid in public and sc.get("cliffhanger")]
    for ep, vid, sc in live[-1:]:  # nur die neueste öffentliche Folge – bei älteren ist die Abstimmung vorbei
        if any(_author(t["snippet"]["topLevelComment"]["snippet"]) == me for t in _threads(vid)):
            continue
        done.append({"episode_id": ep, "kommentar_id": post_top(vid, vote_text(sc))})
    return done


def main(argv):
    cmd = argv[0] if argv else "offen"
    if cmd == "offen":
        rows = open_comments()
        out = db.ROOT / "stats"
        out.mkdir(exist_ok=True)
        (out / "kommentare_offen.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(rows)} offene Kommentare -> stats/kommentare_offen.json")
    elif cmd == "antworten":
        sent, skipped = send(json.loads(open(argv[1], encoding="utf-8").read()))
        print(json.dumps({"gesendet": sent, "uebersprungen": skipped}, ensure_ascii=False, indent=1))
    elif cmd == "abstimmung":
        print(json.dumps(vote_comments(), ensure_ascii=False, indent=1))
    else:
        sys.exit("Befehle: offen | antworten <datei> | abstimmung")


if __name__ == "__main__":
    main(sys.argv[1:])
