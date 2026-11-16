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
