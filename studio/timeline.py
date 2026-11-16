"""Drehbuch -> exakte Zeitleiste (Einstellungsdauern aus den echten Sprachlängen)."""
import copy

from .audio import tts

FPS = 30


def build(script, chars, overrides=None):
    ov = overrides or {}
    g = ov.get("global", {})
    pad_mul = g.get("pad_mul", 1.0)
    gap = g.get("gap", 0.22)
    len_mul = g.get("length_mul", 1.0)
    tl = {"fps": FPS, "shots": [], "label": script.get("label", "")}
    # Alle Chatterbox-Zeilen vorab in einem Rutsch erzeugen (Modell lädt nur einmal)
    reqs = []
    for si, shot in enumerate(script["shots"]):
        for li, ln in enumerate(shot.get("lines", [])):
            lov = ov.get("lines", {}).get(f"{si}.{li}", {})
            reqs.append({"text": ln.get("tts") or ln["text"], "voice": chars[ln["speaker"]]["voice"],
                         "emotion": ln.get("emotion") or ln.get("expr") or "neutral", "fx": ln.get("fx"),
                         "length_mul": len_mul * lov.get("length_mul", 1.0), "seed": lov.get("seed", 1)})
    tts.prepare(reqs)
    t0 = 0.0
    for si, shot in enumerate(script["shots"]):
        s = copy.deepcopy(shot)
        s["_index"] = si
        t = s.get("pad_start", 0.3) * pad_mul
        for li, ln in enumerate(s.get("lines", [])):
            key = f"{si}.{li}"
            lov = ov.get("lines", {}).get(key, {})
            voice = chars[ln["speaker"]]["voice"]
            path, smp = tts.synth(ln.get("tts") or ln["text"], voice, ln.get("emotion") or ln.get("expr") or "neutral",
                                  ln.get("fx"), length_mul=len_mul * lov.get("length_mul", 1.0),
                                  noise=lov.get("noise"), seed=lov.get("seed", 1))
            t += ln.get("delay", 0.0)
            ln["_key"] = key
            ln["_wav"] = str(path)
            ln["_start"] = round(t, 3)
            ln["_dur"] = round(len(smp) / tts.SR, 3)
            ln["_env"] = tts.mouth_envelope(smp, FPS)
            t += ln["_dur"] + ln.get("gap", gap)
        if s.get("lines"):
            t -= s["lines"][-1].get("gap", gap)
        dur = max(t + s.get("pad_end", 0.45) * pad_mul, s.get("min_dur", 1.2))
        if "dur" in s:
            dur = max(dur, s["dur"])
        frames = int(round(dur * FPS))
        s["_frames"] = frames
        s["_dur"] = frames / FPS
        s["_t0"] = round(t0, 4)
        t0 += s["_dur"]
        tl["shots"].append(s)
    tl["duration"] = round(t0, 3)
    return tl
