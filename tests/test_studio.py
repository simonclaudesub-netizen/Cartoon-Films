"""Schnelle Funktionstests:  python -m pytest -q tests  (oder: python tests/test_studio.py)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import db, qc, subtitles, validate  # noqa: E402
from studio.audio import music, sfx  # noqa: E402
from studio.draw import characters as C  # noqa: E402
from studio.draw import sets as S  # noqa: E402
from studio.publish import tiktok, votes, youtube  # noqa: E402
from studio.scene import ShotRenderer  # noqa: E402


def test_every_set_and_character_renders():
    chars = db.characters()
    for name in S.SETS:
        for time in ("day", "night"):
            shot = {"set": name, "time": time, "_dur": 2, "lens": 0.1,
                    "characters": [{"id": cid, "x": i * 0.6 - 0.9, "z": 2.5} for i, cid in enumerate(chars)]}
            surf = ShotRenderer(shot, chars, "TEST").frame(1.0)
            assert surf.get_width() == 1080 and surf.get_height() == 1920


def test_all_expressions_and_poses():
    import cairo
    look = db.character("helga")["look"]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 300, 800)
    ctx = cairo.Context(surf)
    for e in C.EXPRESSIONS:
        for a in C.ARM_POSES:
            C.draw(ctx, look, 150, 780, 1.0, expr=e, arms=a, mouth=0.5)


def test_pov_modes():
    chars = db.characters()
    for mode in ("phone", "door", "box", "table", "knock"):
        shot = {"set": "flur", "_dur": 2, "pov": {"mode": mode, "messages": [{"from": "du", "text": "Hallo", "at": 0}]}}
        ShotRenderer(shot, chars, "").frame(0.0)
        ShotRenderer(shot, chars, "").frame(1.5)


def test_audio_generators():
    for n in validate.SFX:
        x = sfx.make(n)
        assert len(x) > 1000 and abs(x).max() <= 2.0
    for m in validate.MOODS:
        assert len(music.generate(m, 3.0)) == 3 * 48000


def test_subtitle_chunks():
    c = subtitles.chunk("Hallo? Ich bin's, Frau Brandt! Bitte machen Sie auf!")
    assert c == ["Hallo? Ich bin's, Frau Brandt!", "Bitte machen Sie auf!"]
    assert all(len(x) <= subtitles.MAX_CHARS + 8 for x in subtitles.chunk("ein " * 30))


def test_similarity_is_strict_on_word_swaps():
    assert qc.similarity("dann bin das nicht ich", "dann bin das nicht ich") == 1.0
    assert qc.similarity("dann bin das nicht ich", "Fänd ihn das nicht, ich") < 0.75


def test_trailing_babble_and_fillers():
    assert qc.trailing_extra("Ich weiß, dass Sie da sind.", "Ich weiß, dass sie da sind. A, O.") == ["a", "o"]
    assert qc.trailing_extra("Fragen Sie lieber nicht.", "Fragen Sie lieber nicht.") == []
    assert qc.similarity("Äh... und warum?", "Und warum?") == 1.0
    assert qc.similarity("Drei Uhr nachts.", "3 Uhr nachts.") == 1.0


def test_votes():
    cm = [{"author": 1, "text": "A!!"}, {"author": 2, "text": "B"}, {"author": 3, "text": "Option B"},
          {"author": 1, "text": "doch b"}, {"author": 4, "text": "lol"}]
    t = votes.tally(cm, {"A": "Tür öffnen", "B": "Nicht öffnen"})
    assert t["counts"] == {"A": 0, "B": 3} and t["winner"] == "B"


def test_upload_payloads():
    meta = {"title": "T", "description": "D", "hashtags": ["#a", "#shorts"]}
    yt = youtube.build_metadata(meta)
    assert yt["status"]["containsSyntheticMedia"] is True and yt["status"]["privacyStatus"] == "private"
    tk = tiktok.build_post_info(meta, "SELF_ONLY")
    assert tk["is_aigc"] is True and "#shorts" not in tk["title"]
    assert tiktok.chunk_plan(5 * 2 ** 20) == (5 * 2 ** 20, 1)
    cs, n = tiktok.chunk_plan(150 * 2 ** 20)
    assert 5 * 2 ** 20 <= cs <= 64 * 2 ** 20 and n == 15


def test_episode_scripts_validate():
    for ep in db.episodes():
        assert validate.script(ep["id"]) == [], ep["id"]


def test_repeated_words_detected():
    assert qc.trailing_extra("Guten Morgen, Frau Brandt.", "Guten Morgen, Frau Prandt-Prandt.")
    assert qc.trailing_extra("Ja.", "Ja, tschüss tschüss!")
    assert qc.trailing_extra("Niemandem. Niemandem.", "Niemandem, niemandem.") == []


def test_publish_gate_and_slot():
    import datetime as dt
    from zoneinfo import ZoneInfo
    from studio import release
    cfg = release.config()
    tz = ZoneInfo("Europe/Berlin")
    assert release.publish_slot(cfg, dt.datetime(2026, 11, 17, 14, 0, tzinfo=tz)) == "2026-11-17T17:00:00Z"
    assert release.publish_slot(cfg, dt.datetime(2026, 11, 17, 17, 50, tzinfo=tz)) == "2026-11-18T17:00:00Z"
    yt = youtube.build_metadata({"title": "t", "description": "d"}, "public", "2026-11-17T17:00:00Z")
    assert yt["status"]["privacyStatus"] == "private" and yt["status"]["publishAt"]
    # abgelehnte Episoden dürfen nie veröffentlicht werden
    orig = db.status
    db.status = lambda ep: {"state": "abgelehnt", "score": 59}
    try:
        release.publish("wohnung-4b-e01", ["youtube"])
        raise AssertionError("abgelehnte Episode wurde nicht gesperrt")
    except SystemExit:
        pass
    finally:
        db.status = orig


class _Patch:
    """Mini-Ersatz für pytest.monkeypatch (Tests laufen ohne pytest)."""

    def __init__(self):
        self.undo = []

    def setattr(self, obj, name, val):
        self.undo.append((obj, name, getattr(obj, name)))
        setattr(obj, name, val)

    def setenv(self, k, v):
        import os
        self.undo.append((os.environ, k, os.environ.get(k)))
        os.environ[k] = v

    def restore(self):
        import os
        for obj, name, old in reversed(self.undo):
            if obj is os.environ:
                os.environ.pop(name, None) if old is None else os.environ.__setitem__(name, old)
            else:
                setattr(obj, name, old)


def test_tiktok_draft_flow():
    import tempfile
    monkeypatch = _Patch()
    tmp_path = Path(tempfile.mkdtemp())
    try:
        _tiktok_draft_flow(tmp_path, monkeypatch)
    finally:
        monkeypatch.restore()


def _tiktok_draft_flow(tmp_path, monkeypatch):
    """Entwurfs-Upload: init im Postfach-Endpunkt, Stück-Upload, Status SEND_TO_USER_INBOX; Token-Rotation verschlüsselt."""
    from cryptography.fernet import Fernet
    from studio.publish import tiktok
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("TT_TOKEN_KEY", key)
    monkeypatch.setenv("TT_CLIENT_KEY", "ck")
    monkeypatch.setenv("TT_CLIENT_SECRET", "cs")
    monkeypatch.setenv("TT_REFRESH_TOKEN", "rt-alt")
    monkeypatch.setattr(tiktok, "SECRETS", tmp_path / "none.json")
    monkeypatch.setattr(tiktok, "ENC", tmp_path / "tok.enc")
    monkeypatch.setattr(tiktok.time, "sleep", lambda s: None)
    tiktok._ACCESS.clear()
    calls = []

    class R:
        def __init__(self, j, code=200):
            self._j, self.status_code, self.text = j, code, ""

        def json(self):
            return self._j

    def post(url, headers=None, data=None, timeout=None):
        calls.append(url)
        if url.endswith("/oauth/token/"):
            assert data["refresh_token"] == "rt-alt"
            return R({"access_token": "at", "refresh_token": "rt-neu", "expires_in": 86400})
        if url.endswith("/inbox/video/init/"):
            body = json.loads(data)
            assert "post_info" not in body and body["source_info"]["source"] == "FILE_UPLOAD"
            return R({"data": {"publish_id": "p1", "upload_url": "https://up/x"}, "error": {"code": "ok"}})
        if url.endswith("/status/fetch/"):
            return R({"data": {"status": "SEND_TO_USER_INBOX"}, "error": {"code": "ok"}})
        raise AssertionError(url)

    puts = []
    monkeypatch.setattr(tiktok.requests, "post", post)
    monkeypatch.setattr(tiktok.requests, "put", lambda url, data=None, headers=None, timeout=None:
                        puts.append(headers["Content-Range"]) or R({}, 201))
    v = tmp_path / "v.mp4"
    v.write_bytes(b"x" * 1000)
    assert tiktok.configured()
    res = tiktok.upload_draft(v, {"title": "T", "hashtags": ["#a", "#shorts"]})
    assert res["status"] == "SEND_TO_USER_INBOX" and res["mode"] == "entwurf" and res["caption"] == "T #a"
    assert puts == ["bytes 0-999/1000"]
    assert Fernet(key.encode()).decrypt((tmp_path / "tok.enc").read_bytes()).decode() == "rt-neu"
    assert tiktok._secrets()["refresh_token"] == "rt-neu"


def test_voice_fallback_chain():
    """Qwen3 → ZONOS3 → Piper, je nachdem, welches Werkzeug installiert ist."""
    from studio.audio import qwen, tts, zonos
    v = db.character("du")["voice"]
    assert v["engine"] == "qwen3" and v.get("ref_text")
    mp = _Patch()
    try:
        mp.setattr(qwen, "available", lambda: False)
        mp.setattr(zonos, "available", lambda: True)
        assert tts.resolve(v)["engine"] == "zonos"
        mp.setattr(zonos, "available", lambda: False)
        assert tts.resolve(v)["model"] == v["fallback"]["model"]
        mp.setattr(qwen, "available", lambda: True)
        assert tts.resolve(v)["engine"] == "qwen3"
    finally:
        mp.restore()


def test_buffer_schedule():
    """Buffer: Termin -> customScheduled + dueAt, KI-Kennzeichnung immer an, Video per öffentlichem Link."""
    from studio.publish import buffer
    sent = []

    def fake_q(query, variables=None, timeout=60):
        if "organizations" in query:
            return {"account": {"organizations": [{"id": "o1"}]}}
        if "channels" in query:
            return {"channels": [{"id": "c0", "name": "yt", "service": "youtube", "isQueuePaused": False},
                                 {"id": "c1", "name": "tt", "service": "tiktok", "isQueuePaused": False}]}
        sent.append(variables["input"])
        return {"createPost": {"post": {"id": "p1", "dueAt": "2026-11-18T17:00:00.000Z", "status": "scheduled"}}}
    mp = _Patch()
    try:
        mp.setattr(buffer, "_q", fake_q)
        mp.setattr(buffer, "stage_media", lambda v, n: f"https://example.invalid/{n}")
        r = buffer.schedule("x.mp4", "Titel #duentscheidest", "ep.mp4", "2026-11-18T17:00:00Z")
        i = sent[-1]
        assert i["channelId"] == "c1" and i["mode"] == "customScheduled" and i["dueAt"] == "2026-11-18T17:00:00Z"
        assert i["schedulingType"] == "automatic" and i["metadata"]["tiktok"]["isAiGenerated"] is True
        assert i["assets"][0]["video"]["url"].endswith("/ep.mp4") and r["buffer_post_id"] == "p1"
        buffer.schedule("x.mp4", "T", "ep.mp4", None)
        assert sent[-1]["mode"] == "shareNow" and "dueAt" not in sent[-1]
    finally:
        mp.restore()


def test_similarity_numbers_and_clitics():
    """Whisper schreibt Zahlen/Einheiten als Ziffern und verschluckt 's – darf nicht blockieren (Teil 3, 18.11.)."""
    from studio import qc
    assert qc.similarity("Lina? Die wohnt dreihundert Kilometer weit weg.", "Lina, die wohnt 300 km weit weg.") > 0.95
    assert qc.similarity("Ich bin's.", "Ich bin...") > 0.95
    assert qc.similarity("Zweiundzwanzig Mal.", "22 Mal.") > 0.95
    assert qc._norm("Ein Mann") == "ein mann"
    assert qc.similarity("Ich gehe nach Hause.", "Ich gehe nicht.") < qc.LINE_MIN


def test_qwen_lines_get_new_takes():
    """Unverständliche Qwen3-Zeilen bekommen neue Takes (Seed) statt immer derselben Aufnahme (Teil 3, 18.11.)."""
    from studio import pipeline
    from studio.audio import qwen
    mp = _Patch()
    try:
        mp.setattr(qwen, "available", lambda: True)
        assert pipeline.takes_possible(db.character("lina")["voice"])
        res = {"line_tests": [{"ok": False, "key": "5.0", "speaker": "lina", "similarity": 0.83}], "checks": []}
        ov = {}
        actions = pipeline.fixes_for(res, {"shots": []}, ov)
        assert ov["lines"]["5.0"]["seed"] == 2 and "Take" in actions[0]
    finally:
        mp.restore()


def test_comment_replies_guarded():
    """Antworten: nur offene Kommentare, max. 20, keine Links/@/Doppelten (Freigabe 19.11.)."""
    from studio.publish import comments as c
    sent_calls = []
    orig = (c.open_comments, c.reply)
    c.open_comments = lambda: [{"id": f"k{i}"} for i in range(30)]
    c.reply = lambda pid, text: sent_calls.append(pid) or f"r{pid}"
    try:
        ans = [{"id": f"k{i}", "text": f"Antwort {i} 😬"} for i in range(25)]
        ans += [{"id": "k25", "text": "Antwort 1 😬"}, {"id": "fremd", "text": "hallo"},
                {"id": "k26", "text": "schau www.spam.de"}, {"id": "k27", "text": "@jemand hi"}]
        sent, skipped = c.send(ans)
        assert len(sent) == c.MAX_PER_RUN == len(sent_calls)
        gr = " ".join(s["grund"] for s in skipped)
        assert "Grenze" in gr and "nicht (mehr) offen" in gr and "Link" in gr and "@" in gr
        assert "Was soll ich tun?" in c.vote_text({"episode": 4, "cliffhanger": {"options": {"A": "X", "B": "Y"}}})
    finally:
        c.open_comments, c.reply = orig


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("OK  ", name)
            except Exception as e:
                fails += 1
                print("FAIL", name, repr(e))
    sys.exit(1 if fails else 0)
