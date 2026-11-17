"""TikTok Content Posting API – Entwurf ins Postfach (Standard) oder Direct Post.

Geprüft am 16.11.2026 (developers.tiktok.com):
  POST https://open.tiktokapis.com/v2/post/publish/creator_info/query/   (Scope video.publish)
  POST https://open.tiktokapis.com/v2/post/publish/video/init/           -> publish_id, upload_url
  PUT  upload_url  (Content-Range: bytes a-b/total, Content-Type: video/mp4) – 201 wenn komplett
  POST https://open.tiktokapis.com/v2/post/publish/status/fetch/         {"publish_id": ...}
  POST https://open.tiktokapis.com/v2/oauth/token/   (grant_type=refresh_token; liefert NEUEN refresh_token)
post_info.is_aigc = true setzt das Label "KI-generiert".

WICHTIGE EINSCHRÄNKUNGEN (laut offizieller Doku):
  * Unauditierte Apps dürfen nur privat posten ("restricted to private viewing mode").
    Öffentliche Posts erst nach dem TikTok-Audit der App.
  * Kommentare eigener Videos lassen sich mit der normalen Developer-API NICHT lesen
    (Display API: nur user/info, video/list, video/query; Research API nur für akademische Forschung).
    -> TikTok-Abstimmungen werden manuell importiert (siehe votes.py).

ENTWURFS-MODUS (Standard, mode="entwurf"), Scope video.upload:
  POST https://open.tiktokapis.com/v2/post/publish/inbox/video/init/  {"source_info": {...}}
  -> Video landet als Entwurf im TikTok-Postfach; der Mensch tippt auf die Benachrichtigung,
     schaltet "KI-generierte Inhalte" ein und postet. Status "SEND_TO_USER_INBOX" = zugestellt.
  Grenzen: max. 5 offene Entwürfe pro 24 h, 6 Anfragen/Minute.

Zugangsdaten (nie im Repository im Klartext):
  config/secrets/tiktok.json {"client_key", "client_secret", "refresh_token"}
  oder Umgebungsvariablen TT_CLIENT_KEY, TT_CLIENT_SECRET, TT_REFRESH_TOKEN.
  TikTok kann beim Erneuern einen NEUEN refresh_token liefern. Ist TT_TOKEN_KEY gesetzt, wird der
  jeweils neueste Token VERSCHLÜSSELT (Fernet) in config/tiktok_token.enc abgelegt, damit die
  täglichen Cloud-Sitzungen ihn über Git weitergeben können.
"""
import json
import math
import os
import time

import requests

from ..db import ROOT

SECRETS = ROOT / "config" / "secrets" / "tiktok.json"
API = "https://open.tiktokapis.com"
MB = 1024 * 1024


ENC = ROOT / "config" / "tiktok_token.enc"
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
SCOPES = "user.info.basic,video.upload"


def _fernet():
    key = os.environ.get("TT_TOKEN_KEY")
    if not key:
        return None
    from cryptography.fernet import Fernet
    return Fernet(key.encode())


def _secrets():
    s = json.loads(SECRETS.read_text()) if SECRETS.exists() else {}
    for k, env in (("client_key", "TT_CLIENT_KEY"), ("client_secret", "TT_CLIENT_SECRET"),
                   ("refresh_token", "TT_REFRESH_TOKEN")):
        if not s.get(k) and os.environ.get(env):
            s[k] = os.environ[env]
    f = _fernet()
    if f and ENC.exists():  # neuester (rotierter) Token aus dem Repository hat Vorrang
        try:
            s["refresh_token"] = f.decrypt(ENC.read_bytes()).decode()
        except Exception:
            pass
    return s


def _store_refresh(s, new_rt):
    if new_rt == s.get("refresh_token"):
        return
    s["refresh_token"] = new_rt
    if SECRETS.exists():
        SECRETS.write_text(json.dumps(s, indent=2))
        os.chmod(SECRETS, 0o600)
    f = _fernet()
    if f:
        ENC.write_bytes(f.encrypt(new_rt.encode()))


def configured():
    s = _secrets()
    return all(s.get(k) for k in ("client_key", "client_secret", "refresh_token"))


_ACCESS = {}


def _token():
    if _ACCESS.get("expires_at", 0) > time.time() + 120:
        return _ACCESS["token"]
    s = _secrets()
    r = requests.post(f"{API}/v2/oauth/token/", headers={"Content-Type": "application/x-www-form-urlencoded"},
                      data={"client_key": s["client_key"], "client_secret": s["client_secret"],
                            "grant_type": "refresh_token", "refresh_token": s["refresh_token"]}, timeout=30)
    j = r.json()
    if r.status_code != 200 or "access_token" not in j:
        raise RuntimeError(f"TikTok-Token: {r.status_code} {j.get('error')} {j.get('error_description')}")
    _store_refresh(s, j.get("refresh_token") or s["refresh_token"])
    _ACCESS.update(token=j["access_token"], expires_at=time.time() + int(j.get("expires_in", 7200)))
    return j["access_token"]


def auth_url(client_key, redirect_uri, state="studio"):
    from urllib.parse import urlencode
    return AUTH_URL + "?" + urlencode({"client_key": client_key, "scope": SCOPES, "response_type": "code",
                                       "redirect_uri": redirect_uri, "state": state})


def extract_code(text):
    from urllib.parse import parse_qs, unquote, urlparse
    text = text.strip()
    if "code=" in text:
        return unquote(parse_qs(urlparse(text).query).get("code", [""])[0])
    return text


def exchange_code(client_key, client_secret, redirect_uri, code):
    r = requests.post(f"{API}/v2/oauth/token/", headers={"Content-Type": "application/x-www-form-urlencoded"},
                      data={"client_key": client_key, "client_secret": client_secret, "grant_type": "authorization_code",
                            "code": extract_code(code), "redirect_uri": redirect_uri}, timeout=30)
    j = r.json()
    if "refresh_token" not in j:
        raise RuntimeError(f"TikTok-Anmeldung fehlgeschlagen: {j}")
    SECRETS.parent.mkdir(parents=True, exist_ok=True)
    SECRETS.write_text(json.dumps({"client_key": client_key, "client_secret": client_secret,
                                   "refresh_token": j["refresh_token"], "scope": j.get("scope")}, indent=2))
    os.chmod(SECRETS, 0o600)
    return j.get("scope"), j.get("refresh_expires_in")


def _post(path, tok, body):
    r = requests.post(f"{API}{path}", headers={"Authorization": f"Bearer {tok}",
                                                "Content-Type": "application/json; charset=UTF-8"},
                      data=json.dumps(body), timeout=60)
    j = r.json()
    if r.status_code != 200 or j.get("error", {}).get("code", "ok") != "ok":
        raise RuntimeError(f"TikTok {path}: {r.status_code} {j.get('error')}")
    return j["data"]


def chunk_plan(size):
    """Chunk-Regeln: <=64 MB als ein Stück; sonst Stücke à 10 MB, letztes Stück nimmt den Rest (max. 128 MB)."""
    if size <= 64 * MB:
        return size, 1
    cs = 10 * MB
    return cs, size // cs


def build_post_info(meta, privacy):
    tags = [h for h in meta.get("hashtags", []) if h.lower() != "#shorts"]
    caption = (meta["title"] + " " + " ".join(tags)).strip()
    return {"title": caption[:2200], "privacy_level": privacy, "disable_duet": False, "disable_stitch": False,
            "disable_comment": False, "video_cover_timestamp_ms": int(meta.get("cover_ms", 1000)),
            "brand_content_toggle": False, "brand_organic_toggle": False, "is_aigc": True}


def _upload_chunks(url, video_path, size, cs, n):
    with open(video_path, "rb") as f:
        for i in range(n):
            start = i * cs
            end = size - 1 if i == n - 1 else start + cs - 1
            f.seek(start)
            body = f.read(end - start + 1)
            r = requests.put(url, data=body, headers={"Content-Type": "video/mp4", "Content-Length": str(len(body)),
                                                      "Content-Range": f"bytes {start}-{end}/{size}"}, timeout=600)
            if r.status_code not in (200, 201, 206):
                raise RuntimeError(f"TikTok-Upload Stück {i + 1}/{n}: HTTP {r.status_code} {r.text[:200]}")


def upload_draft(video_path, meta=None):
    """Entwurf ins TikTok-Postfach (Scope video.upload). Der Mensch postet in der App."""
    tok = _token()
    size = os.path.getsize(video_path)
    cs, n = chunk_plan(size)
    data = _post("/v2/post/publish/inbox/video/init/", tok, {
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": cs, "total_chunk_count": n}})
    pid = data["publish_id"]
    _upload_chunks(data["upload_url"], video_path, size, cs, n)
    status = "PROCESSING_UPLOAD"
    for _ in range(40):
        time.sleep(6)
        st = _post("/v2/post/publish/status/fetch/", tok, {"publish_id": pid})
        status = st.get("status", status)
        if status in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            break
        if status == "FAILED":
            raise RuntimeError(f"TikTok-Entwurf fehlgeschlagen: {st.get('fail_reason')}")
    return {"platform": "tiktok", "mode": "entwurf", "publish_id": pid, "status": status,
            "caption": build_post_info(meta or {"title": ""}, "SELF_ONLY")["title"]}


def publish(video_path, meta, privacy="SELF_ONLY"):
    tok = _token()
    info = _post("/v2/post/publish/creator_info/query/", tok, {})
    allowed = info.get("privacy_level_options", [])
    if privacy not in allowed:
        privacy = "SELF_ONLY" if "SELF_ONLY" in allowed else allowed[0]
    size = os.path.getsize(video_path)
    cs, n = chunk_plan(size)
    data = _post("/v2/post/publish/video/init/", tok, {
        "post_info": build_post_info(meta, privacy),
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": cs, "total_chunk_count": n}})
    pid = data["publish_id"]
    _upload_chunks(data["upload_url"], video_path, size, cs, n)
    for _ in range(60):
        st = _post("/v2/post/publish/status/fetch/", tok, {"publish_id": pid})
        if st.get("status") == "PUBLISH_COMPLETE":
            return {"platform": "tiktok", "publish_id": pid, "privacy": privacy, "status": st}
        if st.get("status") == "FAILED":
            raise RuntimeError(f"TikTok: Veröffentlichung fehlgeschlagen: {st.get('fail_reason')}")
        time.sleep(5)
    return {"platform": "tiktok", "publish_id": pid, "privacy": privacy, "status": "PROCESSING"}
