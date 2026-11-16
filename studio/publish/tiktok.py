"""TikTok Content Posting API – Direct Post (offizielle Schnittstelle).

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

Zugangsdaten: config/secrets/tiktok.json
  {"client_key": "...", "client_secret": "...", "refresh_token": "..."}
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


def configured():
    return SECRETS.exists() and "refresh_token" in json.loads(SECRETS.read_text())


def _token():
    s = json.loads(SECRETS.read_text())
    if s.get("access_token") and s.get("expires_at", 0) > time.time() + 120:
        return s["access_token"]
    r = requests.post(f"{API}/v2/oauth/token/", headers={"Content-Type": "application/x-www-form-urlencoded"},
                      data={"client_key": s["client_key"], "client_secret": s["client_secret"],
                            "grant_type": "refresh_token", "refresh_token": s["refresh_token"]}, timeout=30)
    r.raise_for_status()
    j = r.json()
    s.update(access_token=j["access_token"], refresh_token=j["refresh_token"],
             expires_at=time.time() + int(j.get("expires_in", 7200)))
    SECRETS.write_text(json.dumps(s, indent=2))  # neuer refresh_token ersetzt den alten
    os.chmod(SECRETS, 0o600)
    return s["access_token"]


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
    pid, url = data["publish_id"], data["upload_url"]
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
    for _ in range(60):
        st = _post("/v2/post/publish/status/fetch/", tok, {"publish_id": pid})
        if st.get("status") == "PUBLISH_COMPLETE":
            return {"platform": "tiktok", "publish_id": pid, "privacy": privacy, "status": st}
        if st.get("status") == "FAILED":
            raise RuntimeError(f"TikTok: Veröffentlichung fehlgeschlagen: {st.get('fail_reason')}")
        time.sleep(5)
    return {"platform": "tiktok", "publish_id": pid, "privacy": privacy, "status": "PROCESSING"}
