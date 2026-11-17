"""TikTok vollautomatisch über Buffer (offizielle Buffer-API, Gratis-Tarif, von TikTok zugelassener Partner).

Ablauf:
  1. Video öffentlich bereitstellen: Branch `tiktok-media` (ein einziger Commit, wird per force-push
     überschrieben, behält nur die letzten KEEP Videos) -> raw.githubusercontent.com-Link.
     Buffer kennt keinen Datei-Upload, sondern holt das Video zum Veröffentlichungszeitpunkt über den Link.
  2. createPost (GraphQL, https://api.buffer.com): schedulingType=automatic, mode=customScheduled + dueAt
     (oder shareNow), metadata.tiktok.isAiGenerated=true (KI-Kennzeichnung).

Zugang: Buffer-API-Schlüssel liegt als Netzwerk-Geheimnis der Cloud-Umgebung (der Proxy setzt den
Authorization-Header ein). Lokal geht auch BUFFER_API_KEY. Nie ins Repository schreiben.
Doku: https://developers.buffer.com/reference.html
"""
import json
import os
import subprocess
import time
from pathlib import Path

import requests

from ..db import ROOT

API = "https://api.buffer.com"
BRANCH = "tiktok-media"
KEEP = 3
REPO_RAW = os.environ.get("STUDIO_MEDIA_RAW", "https://raw.githubusercontent.com/simonclaudesub-netizen/Cartoon-Films")


def _q(query, variables=None, timeout=60):
    key = os.environ.get("BUFFER_API_KEY") or "proxy-injected"  # in der Cloud setzt der Proxy den echten Schlüssel
    r = requests.post(API, json={"query": query, "variables": variables or {}},
                      headers={"Authorization": f"Bearer {key}"}, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"Buffer-API: HTTP {r.status_code} {r.text[:200]}")
    j = r.json()
    if j.get("errors"):
        raise RuntimeError(f"Buffer-API: {j['errors'][0].get('message')}")
    return j["data"]


def tiktok_channel():
    """Erster verbundener TikTok-Kanal (id, name) oder None."""
    for o in _q("query { account { organizations { id } } }")["account"]["organizations"]:
        chans = _q("query($id: OrganizationId!) { channels(input: {organizationId: $id}) "
                   "{ id name service isQueuePaused } }", {"id": o["id"]})["channels"]
        for c in chans:
            if c["service"] == "tiktok":
                return c
    return None


def configured():
    try:
        c = tiktok_channel()
        return bool(c) and not c.get("isQueuePaused")
    except Exception:
        return False


def check():
    """Für `studio check`: (ok, Text)."""
    try:
        c = tiktok_channel()
    except Exception as e:
        return False, f"Buffer nicht erreichbar: {e}"
    if not c:
        return False, "Buffer: kein TikTok-Kanal verbunden"
    ch = _q("query($id: ChannelId!) { channel(input: {id: $id}) { isDisconnected "
            "metadata { ... on TiktokMetadata { defaultToReminders } } } }", {"id": c["id"]})["channel"]
    if ch["isDisconnected"]:
        return False, f"Buffer: TikTok-Kanal {c['name']} getrennt (in Buffer neu verbinden)"
    if c["isQueuePaused"]:
        return False, f"Buffer: Warteschlange von {c['name']} pausiert"
    return True, f"Buffer -> TikTok {c['name']} (automatisch: {not (ch.get('metadata') or {}).get('defaultToReminders')})"


def _git(*a, cwd=ROOT, check=True):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=check)


def stage_media(video_path, name):
    """Legt das Video öffentlich auf den Branch tiktok-media (ein einziger Commit ohne Verlauf, nur die
    letzten KEEP Videos; Reihenfolge in order.json). Gibt den raw-Link zurück."""
    keep = []  # (name, blob) der bisherigen Videos, älteste zuerst
    if _git("fetch", "-q", "origin", BRANCH, check=False).returncode == 0:
        blobs = {}
        for line in _git("ls-tree", "FETCH_HEAD").stdout.splitlines():
            meta, fname = line.split("\t", 1)
            blobs[fname] = meta.split()[2]
        order = json.loads(_git("cat-file", "-p", blobs["order.json"]).stdout) if "order.json" in blobs else sorted(
            f for f in blobs if f.endswith(".mp4"))
        keep = [(f, blobs[f]) for f in order if f in blobs and f != name][-(KEEP - 1):]
    new_blob = _git("hash-object", "-w", str(video_path)).stdout.strip()
    entries = keep + [(name, new_blob)]

    def blob_of(text):
        return subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=ROOT, input=text, capture_output=True,
                              text=True, check=True).stdout.strip()
    readme = blob_of("Nur Zwischenablage für den automatischen TikTok-Upload über Buffer "
                     "(wird bei jeder Folge überschrieben, ohne Verlauf).\n")
    order = blob_of(json.dumps([f for f, _ in entries], indent=1) + "\n")
    tree_txt = "".join(f"100644 blob {b}\t{f}\n" for f, b in
                       sorted(entries + [("README.md", readme), ("order.json", order)]))
    tree = subprocess.run(["git", "mktree"], cwd=ROOT, input=tree_txt, capture_output=True, text=True,
                          check=True).stdout.strip()
    commit = _git("commit-tree", tree, "-m", "TikTok-Medien (Zwischenablage für Buffer)").stdout.strip()
    for i in range(4):
        if _git("push", "-qf", "origin", f"{commit}:refs/heads/{BRANCH}", check=False).returncode == 0:
            break
        time.sleep(2 ** (i + 1))
    else:
        raise RuntimeError("Buffer: Video konnte nicht auf den Branch tiktok-media geschoben werden")
    url = f"{REPO_RAW}/{BRANCH}/{name}"
    size = os.path.getsize(video_path)
    for _ in range(10):  # raw.githubusercontent.com braucht nach dem Push oft ein paar Sekunden
        h = requests.head(url, timeout=30, allow_redirects=True)
        if h.status_code == 200 and int(h.headers.get("content-length", 0)) == size:
            return url
        time.sleep(6)
    raise RuntimeError(f"Buffer: öffentlicher Video-Link nicht erreichbar ({url})")


CREATE = """mutation($input: CreatePostInput!) { createPost(input: $input) {
  ... on PostActionSuccess { post { id dueAt status } }
  ... on MutationError { message } } }"""


def schedule(video_path, caption, name, publish_at=None):
    """Plant den TikTok-Post (publish_at = UTC-ISO, None = sofort). Immer mit KI-Kennzeichnung."""
    c = tiktok_channel()
    if not c:
        raise RuntimeError("Buffer: kein TikTok-Kanal verbunden")
    url = stage_media(video_path, name)
    inp = {"channelId": c["id"], "text": caption, "schedulingType": "automatic", "needsApproval": False,
           "assets": [{"video": {"url": url, "metadata": {"thumbnailOffset": 1000}}}],
           "metadata": {"tiktok": {"isAiGenerated": True}}}
    if publish_at:
        inp.update(mode="customScheduled", dueAt=publish_at)
    else:
        inp["mode"] = "shareNow"
    res = _q(CREATE, {"input": inp})["createPost"]
    if "post" not in res:
        raise RuntimeError(f"Buffer: {res.get('message')}")
    return {"platform": "tiktok", "mode": "buffer", "buffer_post_id": res["post"]["id"],
            "channel": c["name"], "publish_at": publish_at or res["post"]["dueAt"],
            "status": res["post"]["status"], "media_url": url, "caption": caption, "ai_label": True}


def post_status(post_id):
    return _q("query($id: PostId!) { post(input: {id: $id}) { status dueAt sentAt externalLink error { message } } }",
              {"id": post_id})["post"]


if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False))
