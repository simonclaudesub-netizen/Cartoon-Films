"""YouTube Data API v3 – Upload (Shorts) und Kommentare lesen.

Offizielle Endpunkte (geprüft am 16.11.2026):
  Upload:       POST https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status
                -> Location-Header = Upload-URL, dann PUT der Datei (201 Created = fertig)
  Kommentare:   GET  https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId=...
  Token:        POST https://oauth2.googleapis.com/token  (Standard-OAuth-2.0 von Google)
Scopes: youtube.upload (Upload) + youtube.force-ssl (Kommentare) + yt-analytics.readonly (Zuschauerbindung)
Feld status.containsSyntheticMedia = KI-Offenlegung.

Zugangsdaten (nie im Git):
  - lokal: config/secrets/youtube.json  {"client_id": "...", "client_secret": "...", "refresh_token": "..."}
  - im täglichen Cloud-Betrieb: Umgebungsvariablen YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
    (vom Menschen in den Einstellungen der Cloud-Umgebung eingetragen)
  - ein später neu erteilter Refresh-Token (z. B. mit zusätzlichem Analytics-Scope) liegt VERSCHLÜSSELT
    (Fernet, Schlüssel = Umgebungsvariable TT_TOKEN_KEY) in config/youtube_token.enc und hat Vorrang
"""
import json
import os
import time
import urllib.parse

import requests

from ..db import ROOT

SECRETS = ROOT / "config" / "secrets" / "youtube.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]
ENC = ROOT / "config" / "youtube_token.enc"
REDIRECT = "http://localhost:8765/"
TOKEN_URL = "https://oauth2.googleapis.com/token"


ENV = {"client_id": "YT_CLIENT_ID", "client_secret": "YT_CLIENT_SECRET", "refresh_token": "YT_REFRESH_TOKEN"}


def _fernet():
    key = os.environ.get("TT_TOKEN_KEY", "").strip()
    if not key:
        return None
    from cryptography.fernet import Fernet
    return Fernet(key.encode())


def _secrets():
    if SECRETS.exists():
        s = json.loads(SECRETS.read_text())
        if s.get("refresh_token"):
            return s
    s = {k: os.environ.get(v, "").strip() for k, v in ENV.items()}
    f = _fernet()
    if f and ENC.exists():  # neuerer Token (mehr Berechtigungen) aus dem Repository hat Vorrang
        try:
            s["refresh_token"] = f.decrypt(ENC.read_bytes()).decode()
        except Exception:
            pass
    return s if all(s.values()) else None


def configured():
    return _secrets() is not None


def auth_url(client_id):
    q = {"client_id": client_id, "redirect_uri": REDIRECT, "response_type": "code", "scope": " ".join(SCOPES),
         "access_type": "offline", "prompt": "consent"}
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(q)


def extract_code(text):
    """Akzeptiert den reinen Code ODER die komplette Weiterleitungs-Adresse aus dem Browser."""
    text = text.strip()
    if "code=" in text:
        q = urllib.parse.urlparse(text).query or text.split("?", 1)[-1]
        return urllib.parse.parse_qs(q)["code"][0]
    return text


def channel():
    """Prüft den Zugang und liefert den Kanal, auf den hochgeladen wird."""
    r = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "snippet,statistics", "mine": "true"},
                     headers={"Authorization": f"Bearer {_token()}"}, timeout=30)
    r.raise_for_status()
    items = r.json().get("items", [])
    if not items:
        raise RuntimeError("Mit diesem Google-Konto ist kein YouTube-Kanal verbunden.")
    it = items[0]
    return {"id": it["id"], "title": it["snippet"]["title"], "subscribers": it["statistics"].get("subscriberCount")}


def exchange_code(client_id, client_secret, code):
    code = extract_code(code)
    r = requests.post(TOKEN_URL, data={"code": code, "client_id": client_id, "client_secret": client_secret,
                                       "redirect_uri": REDIRECT, "grant_type": "authorization_code"}, timeout=30)
    r.raise_for_status()
    tok = r.json()
    f = _fernet()
    if f:  # für die tägliche Cloud-Sitzung: verschlüsselt ins Repository (config/youtube_token.enc)
        ENC.write_bytes(f.encrypt(tok["refresh_token"].encode()))
    SECRETS.parent.mkdir(parents=True, exist_ok=True)
    SECRETS.write_text(json.dumps({"client_id": client_id, "client_secret": client_secret,
                                   "refresh_token": tok["refresh_token"]}, indent=2))
    os.chmod(SECRETS, 0o600)
    return True


def _token():
    s = _secrets()
    if not s:
        raise RuntimeError("YouTube-Zugangsdaten fehlen (config/secrets/youtube.json oder YT_*-Umgebungsvariablen)")
    r = requests.post(TOKEN_URL, data={"client_id": s["client_id"], "client_secret": s["client_secret"],
                                       "refresh_token": s["refresh_token"], "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def build_metadata(meta, privacy="private", publish_at=None):
    tags = [h.lstrip("#") for h in meta.get("hashtags", [])]
    desc = meta["description"] + (f"\n{meta['credits']}" if meta.get("credits") else "") + "\n\n" + " ".join(meta.get("hashtags", []))
    if "#shorts" not in desc.lower():
        desc += " #Shorts"
    body = {"snippet": {"title": meta["title"][:100], "description": desc[:5000], "tags": tags[:30],
                        "categoryId": "1", "defaultLanguage": "de", "defaultAudioLanguage": "de"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": True, "embeddable": True}}
    if publish_at:  # geplante Veröffentlichung: YouTube verlangt dafür privacyStatus=private
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at
    return body


def upload(video_path, meta, privacy="private", publish_at=None):
    body = build_metadata(meta, privacy, publish_at)
    size = os.path.getsize(video_path)
    tok = _token()
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos",
                      params={"uploadType": "resumable", "part": "snippet,status"},
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                               "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"},
                      data=json.dumps(body), timeout=60)
    r.raise_for_status()
    url = r.headers["Location"]
    for attempt in range(4):
        with open(video_path, "rb") as f:
            up = requests.put(url, data=f, headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4",
                                                    "Content-Length": str(size)}, timeout=600)
        if up.status_code in (200, 201):
            v = up.json()
            return {"platform": "youtube", "id": v["id"], "url": f"https://youtube.com/shorts/{v['id']}",
                    "privacy": body["status"]["privacyStatus"], **({"publish_at": publish_at} if publish_at else {})}
        if up.status_code >= 500:
            time.sleep(2 ** attempt * 5)
            continue
        up.raise_for_status()
    raise RuntimeError("YouTube-Upload nach 4 Versuchen fehlgeschlagen")


def delete(video_id):
    """Video löschen (nur auf ausdrückliche Anweisung des Kanalinhabers, z. B. Ersetzen einer Fassung)."""
    r = requests.delete("https://www.googleapis.com/youtube/v3/videos", params={"id": video_id},
                        headers={"Authorization": f"Bearer {_token()}"}, timeout=30)
    r.raise_for_status()
    return True


def _own_channel(tok):
    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "id", "mine": "true"},
                         headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        return r.json()["items"][0]["id"]
    except Exception:
        return None


def comments(video_id, max_pages=10):
    """Zuschauer-Kommentare (ohne die eigenen des Kanals, z. B. den Abstimmungs-Kommentar)."""
    tok = _token()
    me = _own_channel(tok)
    out, page = [], None
    for _ in range(max_pages):
        params = {"part": "snippet", "videoId": video_id, "maxResults": 100, "textFormat": "plainText"}
        if page:
            params["pageToken"] = page
        r = requests.get("https://www.googleapis.com/youtube/v3/commentThreads", params=params,
                         headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        r.raise_for_status()
        j = r.json()
        for it in j.get("items", []):
            sn = it["snippet"]["topLevelComment"]["snippet"]
            if me and (sn.get("authorChannelId") or {}).get("value") == me:
                continue
            out.append({"author": (sn.get("authorChannelId") or {}).get("value", sn.get("authorDisplayName")),
                        "text": sn.get("textOriginal", ""), "likes": sn.get("likeCount", 0)})
        page = j.get("nextPageToken")
        if not page:
            break
    return out
