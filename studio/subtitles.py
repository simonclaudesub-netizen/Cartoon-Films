"""Untertitel im ASS-Format: kurze, wortgenaue Häppchen im Kurzvideo-Stil."""
import re

SPEAKER_COLORS = {"du": "#FFFFFF", "okan": "#A9D8FF", "helga": "#F9C3E6", "lina": "#FFC9A0"}
MAX_CHARS = 26
MARGIN_V = 470  # Abstand vom unteren Rand -> Unterkante ~ y 1450 (sicher über der TikTok-Beschreibung)


def _ass_color(hexcol):
    h = hexcol.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def _ts(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def chunk(text, max_chars=MAX_CHARS):
    """Teilt eine Zeile in gut lesbare Häppchen: erst an Satzzeichen, lange Sätze dann
    gleichmäßig (keine verwaisten Einzelwörter)."""
    import math
    sentences = [x.strip() for x in re.split(r"(?<=[.!?…])\s+", text) if x.strip()]
    out = []
    for snt in sentences:
        if len(snt) <= max_chars + 4:
            out.append(snt)
            continue
        words = snt.split()
        k = math.ceil(len(snt) / max_chars)
        target = len(snt) / k
        cur = ""
        for w in words:
            cand = (cur + " " + w).strip()
            if cur and len(cand) > target + 3 and len(out) < 1000:
                out.append(cur)
                cur = w
            else:
                cur = cand
        if cur:
            out.append(cur)
    # sehr kurze Satz-Häppchen zusammenfassen ("Hallo?" bleibt, wenn der Rest zu lang wäre)
    merged = []
    for p in out:
        if merged and len(merged[-1]) < 10 and len(merged[-1]) + len(p) + 1 <= max_chars + 4:
            merged[-1] += " " + p
        else:
            merged.append(p)
    return merged


def events(timeline, max_chars=MAX_CHARS):
    ev = []
    for s in timeline["shots"]:
        for ln in s.get("lines", []):
            if ln.get("no_sub"):
                continue
            parts = chunk(ln["text"], max_chars)
            total = sum(len(p) + 6 for p in parts) or 1
            t = s["_t0"] + ln["_start"]
            for p in parts:
                d = ln["_dur"] * (len(p) + 6) / total  # +6: kurze Häppchen bekommen relativ mehr Zeit
                ev.append({"start": round(t, 3), "end": round(t + d, 3), "text": p, "speaker": ln["speaker"],
                           "italic": ln.get("fx") == "inner" or ln.get("emotion") == "whisper"})
                t += d
    # Lücken < 0.25 s schließen (ruhigeres Lesen), Überlappungen verhindern
    for a, b in zip(ev, ev[1:]):
        if 0 < b["start"] - a["end"] < 0.25:
            a["end"] = b["start"]
        if a["end"] > b["start"]:
            a["end"] = b["start"]
    return ev


def write_ass(timeline, path, max_chars=MAX_CHARS):
    ev = events(timeline, max_chars)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Comic Neue,78,&H00FFFFFF,&H00FFFFFF,&H00101010,&H64000000,1,0,0,0,100,100,0,0,1,7,2,2,90,170,{MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for e in ev:
        col = _ass_color(SPEAKER_COLORS.get(e["speaker"], "#FFFFFF"))
        it = r"\i1" if e["italic"] else ""
        pop = r"\fscx92\fscy92\t(0,90,\fscx100\fscy100)"
        lines.append(f"Dialogue: 0,{_ts(e['start'])},{_ts(e['end'])},Sub,{e['speaker']},0,0,0,,"
                     f"{{\\c{col}{it}{pop}}}{e['text']}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")
    return ev
