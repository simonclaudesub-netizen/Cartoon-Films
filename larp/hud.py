"""HUD-Bausteine für den LARP-Kanal: Panels, Kennzahlen, Balken, Sparklines, Code, Logs.

Alles wird mit Cairo als Vektor gezeichnet (Weltkoordinaten 1080 x 1920). Werte, die sich
bewegen sollen, sind Funktionen der Zeit t – damit bleibt jedes Bild reproduzierbar.
"""
import math

import cairo

FONT = "JetBrains Mono"

# Palette (Neon auf Fast-Schwarz) – Szenen können eine eigene Palette übergeben
PAL = {
    "bg": (0.027, 0.027, 0.04),
    "panel": (0.05, 0.05, 0.07),
    "edge": (1, 1, 1),
    "text": (0.86, 0.86, 0.9),
    "dim": (0.42, 0.42, 0.5),
    "accent": (1.0, 0.24, 0.55),     # Pink
    "accent2": (0.71, 0.42, 1.0),    # Violett
    "cyan": (0.44, 0.89, 1.0),
    "green": (0.24, 1.0, 0.6),
    "yellow": (0.9, 1.0, 0.31),
    "white": (0.96, 0.96, 1.0),
}

MONO = dict(PAL, accent=(0.95, 0.95, 0.95), accent2=(0.7, 0.7, 0.7), cyan=(0.85, 0.85, 0.85),
            green=(0.8, 0.8, 0.8), yellow=(0.9, 0.9, 0.9), text=(0.88, 0.88, 0.88), dim=(0.45, 0.45, 0.45))


def hsh(*a):
    """Deterministischer Pseudo-Zufall 0..1 aus beliebigen Zahlen."""
    x = 0
    for v in a:
        x = (x * 1000003 + int(v * 9973) + 0x9E3779B1) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 0x2C1B3C6D) & 0xFFFFFFFF
    x ^= x >> 12
    x = (x * 0x297A2D39) & 0xFFFFFFFF
    x ^= x >> 15
    return x / 0xFFFFFFFF


def noise(t, seed=0.0):
    """Weiches Rauschen -1..1 als Summe von Sinuswellen."""
    return (math.sin(t * 1.7 + seed * 3.1) * 0.5 + math.sin(t * 3.3 + seed * 7.7) * 0.3
            + math.sin(t * 7.1 + seed * 1.3) * 0.2)


def col(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def font(ctx, size, bold=False):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text(ctx, x, y, s, size=13, c=None, a=1.0, bold=False, align="l", pal=PAL):
    font(ctx, size, bold)
    col(ctx, c or pal["text"], a)
    if align != "l":
        w = ctx.text_extents(s).x_advance
        x -= w if align == "r" else w / 2
    ctx.move_to(x, y)
    ctx.show_text(s)


def tw(ctx, s, size, bold=False):
    font(ctx, size, bold)
    return ctx.text_extents(s).x_advance


def rect(ctx, x, y, w, h, c, a=1.0):
    col(ctx, c, a)
    ctx.rectangle(x, y, w, h)
    ctx.fill()


def frame(ctx, x, y, w, h, c, a=0.2, lw=1.2):
    col(ctx, c, a)
    ctx.set_line_width(lw)
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h - 1)
    ctx.stroke()


def panel(ctx, x, y, w, h, title="", right="", pal=PAL, hot=False, alpha=0.9):
    """Dunkles Panel mit Titelzeile wie im Agent-Dashboard."""
    rect(ctx, x, y, w, h, pal["panel"], alpha)
    frame(ctx, x, y, w, h, pal["accent"] if hot else pal["edge"], 0.55 if hot else 0.13)
    # Eck-Markierungen
    col(ctx, pal["edge"], 0.45)
    ctx.set_line_width(1.5)
    for cx, cy, dx, dy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        ctx.move_to(cx + dx * 7, cy)
        ctx.line_to(cx, cy)
        ctx.line_to(cx, cy + dy * 7)
    ctx.stroke()
    if title:
        rect(ctx, x + 10, y + 13, 6, 6, pal["accent"] if hot else pal["white"], 0.9)
        text(ctx, x + 22, y + 21, title, 15, pal["white"], 0.95, bold=True)
    if right:
        text(ctx, x + w - 10, y + 21, right, 12, pal["dim"], align="r")
    return y + 34


def kv(ctx, x, y, w, rows, size=13, gap=19, pal=PAL, vcol=None):
    """Schlüssel/Wert-Zeilen: Schlüssel gedimmt links, Wert rechts."""
    for i, row in enumerate(rows):
        k, v = row[0], row[1]
        c = row[2] if len(row) > 2 else (vcol or pal["text"])
        text(ctx, x, y + i * gap, k, size, pal["dim"], pal=pal)
        text(ctx, x + w, y + i * gap, v, size, c, align="r", pal=pal)
    return y + len(rows) * gap


def bars(ctx, x, y, w, h, n, t, seed=0, pal=PAL, palette=None, speed=1.0, gap=2):
    """Animierte Balken-Histogramme (Unterkante bei y+h)."""
    palette = palette or (pal["accent"], pal["white"], pal["cyan"], pal["yellow"], pal["green"])
    bw = (w - gap * (n - 1)) / n
    for i in range(n):
        base = 0.25 + 0.6 * hsh(seed, i)
        v = base + 0.25 * noise(t * speed * 2 + i * 0.37, seed + i)
        v = max(0.06, min(1.0, v))
        c = palette[int(hsh(seed + 7, i) * len(palette)) % len(palette)]
        rect(ctx, x + i * (bw + gap), y + h - v * h, bw, v * h, c, 0.9)


def spark(ctx, x, y, w, h, t, seed=0, c=None, n=40, lw=1.6, speed=1.0, pal=PAL, a=0.95):
    c = c or pal["accent"]
    col(ctx, c, a)
    ctx.set_line_width(lw)
    for i in range(n):
        u = i / (n - 1)
        v = 0.5 + 0.38 * noise(u * 9 + t * speed * 2.0, seed) + 0.1 * math.sin(u * 40 + seed)
        px, py = x + u * w, y + h - max(0, min(1, v)) * h
        (ctx.line_to if i else ctx.move_to)(px, py)
    ctx.stroke()


def progress(ctx, x, y, w, h, v, c=None, pal=PAL, segs=0):
    rect(ctx, x, y, w, h, pal["white"], 0.08)
    if segs:
        sw = w / segs
        for i in range(int(v * segs)):
            rect(ctx, x + i * sw + 1, y, sw - 2, h, c or pal["white"], 0.85)
    else:
        rect(ctx, x, y, w * max(0, min(1, v)), h, c or pal["white"], 0.9)


def kpi(ctx, x, y, w, h, label, value, sub="", t=0, seed=0, pal=PAL, vcol=None, spark_on=True, vsize=58):
    rect(ctx, x, y, w, h, pal["panel"], 0.92)
    frame(ctx, x, y, w, h, pal["edge"], 0.13)
    text(ctx, x + 12, y + 22, label, 12, pal["dim"], pal=pal)
    text(ctx, x + 12, y + 22 + vsize, value, vsize, vcol or pal["white"], bold=True, pal=pal)
    if spark_on:
        spark(ctx, x + w * 0.58, y + 34, w * 0.38, vsize - 6, t, seed, pal["accent"], pal=pal)
    if sub:
        text(ctx, x + 12, y + h - 12, sub, 11, pal["dim"], pal=pal)


KEYW = {"def", "async", "await", "for", "in", "if", "else", "return", "import", "from", "while", "not",
        "and", "or", "class", "assert", "with", "as", "True", "False", "None", "lambda"}


def code(ctx, x, y, w, h, lines, t, cps=38.0, size=13, pal=PAL, start=0.0, lineno=1, hl_line=None):
    """Code-Editor mit Tipp-Animation, Zeilennummern, Syntaxfarben und Cursor."""
    lh = size * 1.48
    chars = max(0, int((t - start) * cps))
    shown, total = [], 0
    for ln in lines:
        if total >= chars:
            break
        shown.append(ln[:max(0, chars - total)])
        total += len(ln) + 1
    max_lines = int(h / lh)
    off = max(0, len(shown) - max_lines)
    font(ctx, size)
    cw = ctx.text_extents("M").x_advance
    for i, ln in enumerate(shown[off:]):
        yy = y + (i + 1) * lh
        n = off + i
        if hl_line is not None and n == hl_line:
            rect(ctx, x, yy - lh + 4, w, lh, pal["accent"], 0.18)
        text(ctx, x + 2, yy, f"{lineno + n:>3}", size - 1, pal["dim"], 0.6, pal=pal)
        _code_line(ctx, x + cw * 5, yy, ln, size, pal)
    if shown and (int(t * 2.5) % 2 == 0):
        last = shown[-1]
        yy = y + (len(shown) - off) * lh
        rect(ctx, x + cw * 5 + cw * len(last), yy - size, cw * 0.9, size * 1.25, pal["accent"], 0.95)


def _code_line(ctx, x, y, ln, size, pal):
    font(ctx, size)
    cw = ctx.text_extents("M").x_advance
    if ln.lstrip().startswith("#"):
        text(ctx, x, y, ln, size, pal["dim"], 0.8, pal=pal)
        return
    i, cx = 0, x
    while i < len(ln):
        ch = ln[i]
        if ch in "\"'":
            j = ln.find(ch, i + 1)
            j = len(ln) if j < 0 else j + 1
            tok, c = ln[i:j], pal["yellow"]
        elif ch.isalpha() or ch == "_":
            j = i
            while j < len(ln) and (ln[j].isalnum() or ln[j] in "_."):
                j += 1
            tok = ln[i:j]
            c = pal["accent"] if tok in KEYW else (pal["cyan"] if j < len(ln) and ln[j] == "(" else pal["text"])
        elif ch.isdigit():
            j = i
            while j < len(ln) and (ln[j].isdigit() or ln[j] == "."):
                j += 1
            tok, c = ln[i:j], pal["accent2"]
        elif ch == "#":
            tok, c, j = ln[i:], pal["dim"], len(ln)
        else:
            tok, c, j = ch, pal["text"], i + 1
        if tok.strip():
            text(ctx, cx, y, tok, size, c, pal=pal)
        cx += cw * len(tok)
        i = j


def log(ctx, x, y, w, h, entries, t, rate=4.0, size=12, pal=PAL, cols=None):
    """Scrollendes Live-Log. entries: Liste von Tupeln (Spalten); neue Zeile alle 1/rate s."""
    lh = size * 1.55
    n = int(h / lh)
    k = int(t * rate)
    cols = cols or [0, 0.18, 0.42]
    for i in range(n):
        idx = k - n + 1 + i
        if idx < 0:
            continue
        e = entries[idx % len(entries)]
        yy = y + (i + 1) * lh
        fresh = i == n - 1
        if fresh:
            rect(ctx, x - 4, yy - lh + 4, w + 8, lh, pal["accent"], 0.16)
        for j, part in enumerate(e):
            c = pal["dim"] if j == 0 else (pal["accent"] if (j == 1 and fresh) else pal["text"])
            if isinstance(part, tuple):
                part, c = part
            text(ctx, x + cols[j] * w if j < len(cols) else x + w, yy, part, size, c, pal=pal,
                 align="r" if j >= len(cols) else "l")


def heat(ctx, x, y, w, h, nx, ny, t, seed=0, pal=PAL):
    cw, ch = w / nx, h / ny
    for i in range(nx):
        for j in range(ny):
            v = hsh(seed, i, j, int(t * 3 + hsh(i, j) * 5))
            c = pal["accent"] if v > 0.55 else (pal["white"] if v > 0.85 else pal["accent2"])
            a = 0.15 + 0.85 * v if v > 0.3 else 0.08
            rect(ctx, x + i * cw + 2, y + j * ch + 2, cw - 4, ch - 4, c, a)


def gauge(ctx, cx, cy, r, v, pal=PAL, lw=8):
    col(ctx, pal["white"], 0.1)
    ctx.set_line_width(lw)
    ctx.arc(cx, cy, r, math.pi * 0.8, math.pi * 2.2)
    ctx.stroke()
    col(ctx, pal["white"], 0.9)
    ctx.arc(cx, cy, r, math.pi * 0.8, math.pi * (0.8 + 1.4 * v))
    ctx.stroke()
    a = math.pi * (0.8 + 1.4 * v)
    col(ctx, pal["accent"], 1)
    ctx.set_line_width(2.5)
    ctx.move_to(cx, cy)
    ctx.line_to(cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85)
    ctx.stroke()


def wave(ctx, x, y, w, h, t, seed=0, c=None, pal=PAL, lw=2.0, a=0.95, amp=0.4, freq=6.0):
    col(ctx, c or pal["accent"], a)
    ctx.set_line_width(lw)
    for i in range(80):
        u = i / 79
        v = 0.5 + amp * noise(u * freq + t * 1.8, seed)
        (ctx.line_to if i else ctx.move_to)(x + u * w, y + h * (1 - v))
    ctx.stroke()


def tag(ctx, x, y, s, pal=PAL, c=None, size=11, a=0.95):
    """Kleines Label (z.B. Nummern an Datenströmen)."""
    w = tw(ctx, s, size) + 10
    rect(ctx, x - w / 2, y - size - 2, w, size + 8, c or pal["panel"], a)
    frame(ctx, x - w / 2, y - size - 2, w, size + 8, pal["edge"], 0.25)
    text(ctx, x, y + 1, s, size, pal["text"], align="c", pal=pal)


def callout(ctx, x, y, title, sub="", pal=PAL, inverted=False, size=15):
    """Weißes/umrandetes Label mit Pfeil-Text wie 'GATE 0.85'."""
    w = max(tw(ctx, title, size, True), tw(ctx, sub, size - 4)) + 28
    h = size + 18 + (size + 4 if sub else 0)
    if inverted:
        rect(ctx, x, y, w, h, pal["white"], 0.97)
        text(ctx, x + 14, y + size + 7, title, size, pal["bg"], bold=True, pal=pal)
        if sub:
            text(ctx, x + 14, y + size * 2 + 11, sub, size - 4, pal["bg"], 0.8, pal=pal)
    else:
        rect(ctx, x, y, w, h, pal["bg"], 0.9)
        frame(ctx, x, y, w, h, pal["white"], 0.85, 1.5)
        rect(ctx, x + 10, y + size / 2 + 3, 6, 6, pal["white"])
        text(ctx, x + 22, y + size + 7, title, size, pal["white"], bold=True, pal=pal)
        if sub:
            text(ctx, x + 22, y + size * 2 + 11, sub, size - 4, pal["dim"], pal=pal)
    return w, h


def ticker(n, t, rate, digits=0):
    """Hochzählender Zähler."""
    v = n + t * rate
    return f"{v:,.{digits}f}"
