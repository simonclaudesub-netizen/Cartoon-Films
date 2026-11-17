"""Parametrische Cartoon-Figuren.

Eine Figur wird vollständig durch ihr `look`-Objekt aus der Charakter-Datenbank
beschrieben. Dadurch sieht sie in jeder Episode exakt gleich aus
(Figurenkonsistenz ist technisch garantiert, nicht nur "angestrebt").

Lokales Koordinatensystem: Füße bei y=0, nach oben negativ. Eine Figur mit
height=1.0 ist ca. 760 Einheiten hoch (= ca. 1,75 m).
"""
import math

from . import prims as P

UNITS_PER_M = 760 / 1.75
SIL = "#17171c"

EXPRESSIONS = ["neutral", "happy", "angry", "scared", "surprised", "suspicious", "sad", "smirk", "creepy"]

# Armhaltungen: (Oberarm-Winkel, Unterarm-Winkel) je Seite, 0 = gerade nach unten,
# positiv = vom Körper weg. Reihenfolge: (links, rechts)
ARM_POSES = {
    "down": ((0.14, 0.06), (0.14, 0.06)),
    "hips": ((0.62, -0.95), (0.62, -0.95)),
    "wave": ((0.14, 0.06), (2.25, 2.95)),
    "point": ((0.14, 0.06), (1.35, 1.45)),
    "hold": ((0.18, -1.25), (0.18, -1.25)),
    "shrug": ((0.75, 2.0), (0.75, 2.0)),
    "keys": ((0.14, 0.06), (0.35, -1.85)),
    "raise": ((0.14, 0.06), (0.5, 2.6)),
    "cross": ((0.25, -1.55), (0.25, -1.65)),
}


def _dir(a, side):
    return (side * math.sin(a), math.cos(a))


def scale_for(cam, z, look):
    return cam.scale(z) / UNITS_PER_M * look.get("height", 1.0)


def draw(ctx, look, x, y, s, pose="stand", expr="neutral", mouth=0.0, blink=0.0, t=0.0,
         arms="down", prop=None, look_dir=0.0, silhouette=False, talking=False, lit=1.0,
         head_tilt=0.0, back=False):
    """Figur zeichnen. (x, y) = Fußpunkt auf dem Bildschirm, s = Skalierung."""
    L = dict(look)
    if silhouette:
        for k in ("skin", "hair", "top_color", "shirt_color", "pants_color", "shoe_color", "accent"):
            L[k] = SIL
    bw = L.get("build", 1.0)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if pose == "sit":
        ctx.translate(0, 150)
    breathe = 1 + 0.012 * math.sin(t * 2.2)
    sh_y = -555 * breathe
    hip_y = -330
    sw, hw = 100 * bw, 82 * bw

    if pose != "sit":
        _legs(ctx, L, hip_y, hw)
    _hood_back(ctx, L, sh_y)
    # Hals
    P.rrect(ctx, -22, sh_y - 50, 44, 70, 14, L["skin"])
    _torso(ctx, L, sh_y, hip_y, sw, hw)
    # Kopf (mit leichtem Nicken beim Sprechen)
    nod = (0.035 * math.sin(t * 9.0) if talking else 0.0) + 0.02 * math.sin(t * 1.3) + head_tilt
    ctx.save()
    ctx.translate(0, sh_y - 26)
    ctx.rotate(nod)
    ctx.translate(look_dir * 6, 0)
    _head(ctx, L, expr, mouth, blink, look_dir, silhouette, t, back)
    ctx.restore()
    _arms(ctx, L, sh_y, sw, arms, prop, t, talking)
    ctx.restore()


# ---------------------------------------------------------------- Körper
def _legs(ctx, L, hip_y, hw):
    pants, shoe = L["pants_color"], L["shoe_color"]
    for side in (-1, 1):
        x0 = side * hw * 0.48
        P.limb(ctx, [(x0, hip_y + 10), (side * hw * 0.52, -30)], 62, pants)
        P.ellipse(ctx, side * hw * 0.55, -14, 44, 20, shoe)
    # Schritt-Abdeckung
    P.poly(ctx, [(-hw, hip_y - 20), (hw, hip_y - 20), (hw * 0.9, hip_y + 60), (0, hip_y + 75),
                 (-hw * 0.9, hip_y + 60)], pants, P.LW)
    P.line(ctx, [(0, hip_y + 20), (0, hip_y + 72)], 4)


def _hood_back(ctx, L, sh_y):
    if L.get("top") == "hoodie":
        P.blob(ctx, [(-70, sh_y + 10), (-60, sh_y - 45), (0, sh_y - 62), (60, sh_y - 45), (70, sh_y + 10),
                     (0, sh_y + 30)], P.shade(L["top_color"], 0.85))


def _torso_path(ctx, sh_y, hip_y, sw, hw):
    ctx.move_to(-sw, sh_y + 38)
    ctx.curve_to(-sw, sh_y + 5, -sw + 20, sh_y, -sw + 45, sh_y)
    ctx.line_to(sw - 45, sh_y)
    ctx.curve_to(sw - 20, sh_y, sw, sh_y + 5, sw, sh_y + 38)
    ctx.line_to(hw + 4, hip_y + 8)
    ctx.curve_to(hw * 0.5, hip_y + 18, -hw * 0.5, hip_y + 18, -hw - 4, hip_y + 8)
    ctx.close_path()


def _torso(ctx, L, sh_y, hip_y, sw, hw):
    top, shirt = L["top_color"], L.get("shirt_color", "#eeeeee")
    style = L.get("top", "shirt")
    _torso_path(ctx, sh_y, hip_y, sw, hw)
    P.fill_stroke(ctx, top)
    # Schatten-Band (Cel-Shading)
    ctx.save()
    _torso_path(ctx, sh_y, hip_y, sw, hw)
    ctx.clip()
    P.set_col(ctx, P.shade(top, 0.82))
    ctx.rectangle(-sw - 10, hip_y - 45, 2 * sw + 20, 80)
    ctx.fill()
    ctx.restore()
    _torso_path(ctx, sh_y, hip_y, sw, hw)
    P.fill_stroke(ctx, None)
    cy = sh_y
    if style == "cardigan":
        P.poly(ctx, [(-34, cy - 2), (34, cy - 2), (12, hip_y + 12), (-12, hip_y + 12)], shirt)
        P.poly(ctx, [(-34, cy - 2), (-12, cy + 70), (-22, cy + 4)], P.shade(top, 0.9), 4)
        P.poly(ctx, [(34, cy - 2), (12, cy + 70), (22, cy + 4)], P.shade(top, 0.9), 4)
        for i in range(3):
            P.ellipse(ctx, -24, cy + 90 + i * 45, 5, 5, P.shade(top, 0.6), 3)
    elif style == "overall":
        P.rrect(ctx, -58, cy + 55, 116, 120, 10, P.shade(top, 0.95), 4)
        P.rrect(ctx, -30, cy + 80, 60, 45, 6, P.shade(top, 0.85), 4)
        for side in (-1, 1):
            P.line(ctx, [(side * 50, cy + 2), (side * 52, cy + 58)], 4)
            P.ellipse(ctx, side * 50, cy + 62, 6, 6, "#d8c06a", 3)
        P.poly(ctx, [(-32, cy - 2), (32, cy - 2), (0, cy + 30)], shirt, 4)
    elif style == "hoodie":
        P.poly(ctx, [(-30, cy - 2), (30, cy - 2), (0, cy + 26)], P.shade(top, 0.75), 4)
        P.line(ctx, [(-14, cy + 12), (-16, cy + 80)], 4)
        P.line(ctx, [(14, cy + 12), (16, cy + 80)], 4)
        P.poly(ctx, [(-62, hip_y - 70), (62, hip_y - 70), (72, hip_y - 8), (-72, hip_y - 8)], P.shade(top, 0.93), 4)
    elif style == "jacket":
        P.line(ctx, [(0, cy + 4), (0, hip_y + 14)], 4)
        P.poly(ctx, [(-40, cy - 6), (-4, cy + 2), (-22, cy + 40)], P.shade(top, 0.88), 4)
        P.poly(ctx, [(40, cy - 6), (4, cy + 2), (22, cy + 40)], P.shade(top, 0.88), 4)
        P.rrect(ctx, -70, cy + 100, 42, 8, 3, P.shade(top, 0.7), 3)
        P.rrect(ctx, 28, cy + 100, 42, 8, 3, P.shade(top, 0.7), 3)
    else:  # shirt
        P.poly(ctx, [(-30, cy - 4), (0, cy + 26), (-4, cy + 40), (-36, cy + 14)], P.shade(top, 1.15), 4)
        P.poly(ctx, [(30, cy - 4), (0, cy + 26), (4, cy + 40), (36, cy + 14)], P.shade(top, 1.15), 4)
        for i in range(3):
            P.ellipse(ctx, 0, cy + 60 + i * 50, 4, 4, P.shade(top, 0.6), 2.5)
    if L.get("necklace"):
        ctx.arc(0, cy + 10, 30, 0.2, math.pi - 0.2)
        P.ink(ctx, 3)
        ctx.stroke()
    if L.get("name_tag"):
        P.rrect(ctx, 30, cy + 70, 50, 26, 4, "#f4f1e6", 3)


# ---------------------------------------------------------------- Arme
def _arms(ctx, L, sh_y, sw, arms, prop, t, talking):
    pose = ARM_POSES.get(arms, ARM_POSES["down"])
    hands = []
    for i, side in enumerate((-1, 1)):
        a1, a2 = pose[i]
        if arms == "wave" and side == 1:
            a2 += 0.35 * math.sin(t * 10)
        if talking and arms == "down" and side == 1:
            a1 += 0.15 + 0.1 * math.sin(t * 4)
            a2 -= 0.9 + 0.2 * math.sin(t * 4)
        sx, sy = side * (sw - 20), sh_y + 30
        d1 = _dir(a1, side)
        ex, ey = sx + d1[0] * 125, sy + d1[1] * 125
        d2 = _dir(a2, side)
        hx, hy = ex + d2[0] * 112, ey + d2[1] * 112
        P.limb(ctx, [(sx, sy), (ex, ey), (hx, hy)], 42, L["top_color"])
        P.ellipse(ctx, hx - d2[0] * 8, hy - d2[1] * 8, 24, 13, P.shade(L["top_color"], 0.85), 4,
                  rot=math.atan2(d2[1], d2[0]) + math.pi / 2)
        hands.append((hx + d2[0] * 10, hy + d2[1] * 10, math.atan2(d2[1], d2[0]), side))
    if prop:
        _prop(ctx, prop, hands, L)
    for hx, hy, ang, side in hands:
        if prop == "keys" and side == 1:
            continue
        _hand(ctx, hx, hy, ang, side, L["skin"])


def _hand(ctx, x, y, ang, side, skin):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang - math.pi / 2)
    P.blob(ctx, [(-19, -8), (-18, 14), (-9, 26), (2, 28), (13, 25), (19, 12), (18, -8), (0, -14)], skin)
    P.blob(ctx, [(side * 14, -6), (side * 30, 2), (side * 28, 12), (side * 16, 8)], skin, 4)
    for fx in (-8, 0, 8):
        P.line(ctx, [(fx, 14), (fx, 26)], 3)
    ctx.restore()


def _prop(ctx, prop, hands, L):
    (lx, ly, _, _), (rx, ry, _, _) = hands
    cx, cy = (lx + rx) / 2, (ly + ry) / 2
    if prop == "cake":
        P.ellipse(ctx, cx, cy + 6, 95, 22, "#f2f2f2")
        P.poly(ctx, [(cx - 70, cy - 4), (cx - 70, cy - 64), (cx + 70, cy - 64), (cx + 70, cy - 4)], "#c58a4a")
        P.ellipse(ctx, cx, cy - 64, 70, 16, "#f6efe4")
        P.ellipse(ctx, cx, cy - 4, 70, 16, "#c58a4a")
        P.poly(ctx, [(cx - 70, cy - 30), (cx + 70, cy - 30)], None, 4, close=False)
        for dx in (-40, 0, 40):
            P.ellipse(ctx, cx + dx, cy - 70, 9, 8, "#c4283a", 3)
    elif prop == "box":
        P.poly(ctx, [(cx - 95, cy - 120), (cx + 95, cy - 120), (cx + 95, cy + 20), (cx - 95, cy + 20)], "#c9a26b")
        P.poly(ctx, [(cx - 95, cy - 120), (cx + 95, cy - 120), (cx + 75, cy - 150), (cx - 75, cy - 150)], "#d9b77f")
        P.rrect(ctx, cx - 18, cy - 120, 36, 140, 0, "#e5d3a8", 3)
    elif prop == "keys":
        x, y = rx, ry
        P.ellipse(ctx, x, y - 8, 14, 14, None, 4)
        for i, a in enumerate((-0.5, 0.1, 0.7)):
            kx, ky = x + math.sin(a) * 40, y + 18 + math.cos(a) * 30
            P.line(ctx, [(x, y + 4), (kx, ky)], 3)
            P.rrect(ctx, kx - 7, ky - 4, 14, 32, 4, ["#d7b94a", "#c0c0c8", "#b07a3a"][i], 3)
        _hand(ctx, x, y - 26, -math.pi / 2, 1, L["skin"])
    elif prop == "letter":
        P.poly(ctx, [(cx - 60, cy - 70), (cx + 60, cy - 75), (cx + 64, cy + 10), (cx - 58, cy + 14)], "#f4f1e6", 4)
        for i in range(4):
            P.line(ctx, [(cx - 44, cy - 50 + i * 15), (cx + 40, cy - 52 + i * 15)], 2.5, "#7a7a80")
    elif prop == "phone":
        P.rrect(ctx, rx - 26, ry - 70, 52, 92, 9, "#2a2a30", 4)
        P.rrect(ctx, rx - 20, ry - 62, 40, 72, 5, "#6fb4e8", 0)


# ---------------------------------------------------------------- Kopf
HX, HY = 64, 78  # Kopf-Halbachsen
HC = -78        # Kopfmitte relativ zum Kopf-Ursprung (Halsansatz)


def _head(ctx, L, expr, mouth, blink, look_dir, silhouette, t, back=False):
    skin, hair = L["skin"], L["hair"]
    style = L.get("hair_style", "short")
    c = HC
    # Hinter dem Kopf liegende Haare
    if style == "long":
        P.blob(ctx, [(-HX - 14, c - 30), (-HX - 22, c + 80), (-HX + 10, c + 115), (HX - 10, c + 115),
                     (HX + 22, c + 80), (HX + 14, c - 30), (0, c - HY - 14)], hair)
    elif style == "bun":
        P.ellipse(ctx, 0, c - HY - 18, 40, 32, hair)
        P.line(ctx, [(-22, c - HY - 22), (18, c - HY - 10)], 3)
    elif style == "ponytail":
        P.blob(ctx, [(HX - 6, c - 40), (HX + 40, c - 10), (HX + 46, c + 60), (HX + 22, c + 90), (HX + 6, c + 20)], hair)
    # Ohren
    for side in (-1, 1):
        P.ellipse(ctx, side * (HX - 2), c + 6, 14, 20, skin, 4)
        if L.get("earrings"):
            P.ellipse(ctx, side * (HX - 2), c + 30, 5, 5, "#e8c547", 3)
    # Kopfform
    P.ellipse(ctx, 0, c, HX, HY, skin)
    if back:
        # Rückenansicht: Hinterkopf (Haare), kein Gesicht
        if style != "bald":
            P.ellipse(ctx, 0, c - 4, HX, HY * 0.92, hair)
        if style in ("cap", "beanie"):
            _hair_front(ctx, L, style, hair, c)
        return
    if not silhouette:
        # Wangenschatten
        ctx.save()
        P.ellipse_path(ctx, 0, c, HX, HY)
        ctx.clip()
        P.set_col(ctx, P.shade(skin, 0.88))
        P.ellipse_path(ctx, -HX * 0.9, c + 20, 20, 60)
        ctx.fill()
        ctx.restore()
        P.ellipse_path(ctx, 0, c, HX, HY)
        P.fill_stroke(ctx, None)
    _face(ctx, L, expr, mouth, blink, look_dir, silhouette, c)
    _hair_front(ctx, L, style, hair, c)
    if L.get("glasses") and not silhouette:
        for side in (-1, 1):
            P.ellipse(ctx, side * 25, c - 6, 21, 19, (0.85, 0.9, 0.95), 4, alpha=0.18)
        P.line(ctx, [(-5, c - 8), (5, c - 8)], 4)


def _face(ctx, L, expr, mouth, blink, look_dir, silhouette, c):
    eye_y = c - 6
    if silhouette:
        for side in (-1, 1):
            P.ellipse(ctx, side * 24, eye_y, 9, 6, "#f5f5f0", 0)
        if expr == "creepy":
            ctx.move_to(-28, c + 38)
            ctx.curve_to(-10, c + 52, 10, c + 52, 28, c + 38)
            P.ink(ctx, 0)
            P.set_col(ctx, "#f5f5f0")
            ctx.set_line_width(5)
            ctx.stroke()
        return
    big = expr in ("surprised", "scared")
    ew, eh = (14, 19) if big else (13, 16)
    pr = 6.5 if big else 8.5
    for side in (-1, 1):
        ex = side * 24
        if blink > 0.5:
            ctx.move_to(ex - ew, eye_y)
            ctx.curve_to(ex - ew / 2, eye_y + 6, ex + ew / 2, eye_y + 6, ex + ew, eye_y)
            P.ink(ctx, 4)
            ctx.stroke()
            continue
        P.ellipse(ctx, ex, eye_y, ew, eh, "#ffffff", 3.5)
        px = ex + look_dir * 5
        P.ellipse(ctx, px, eye_y + 2, pr, pr, L.get("eye", "#1d1612"), 0)
        P.ellipse(ctx, px - 2.5, eye_y - 1.5, 2.2, 2.2, "#ffffff", 0)
        # Augenlider je nach Ausdruck
        lid = {"angry": 0.45, "suspicious": 0.55, "sad": 0.35, "smirk": 0.3, "creepy": 0.2}.get(expr, 0.0)
        if lid:
            ctx.save()
            P.ellipse_path(ctx, ex, eye_y, ew, eh)
            ctx.clip()
            P.set_col(ctx, L["skin"])
            if expr == "angry":
                ctx.move_to(ex - ew - 2, eye_y - eh - 2)
                ctx.line_to(ex + ew + 2, eye_y - eh - 2)
                ctx.line_to(ex - side * ew, eye_y - eh + 2 * eh * lid)
                ctx.line_to(ex + side * ew, eye_y - eh + 2 * eh * lid * 0.4)
            else:
                ctx.rectangle(ex - ew - 2, eye_y - eh - 2, 2 * ew + 4, 2 * eh * lid + 2)
            ctx.fill()
            ctx.restore()
            P.line(ctx, [(ex - ew, eye_y - eh + 2 * eh * lid), (ex + ew, eye_y - eh + 2 * eh * lid)], 3.5)
        if expr == "happy":
            ctx.move_to(ex - ew, eye_y + eh * 0.6)
            ctx.curve_to(ex - ew / 2, eye_y + eh * 0.1, ex + ew / 2, eye_y + eh * 0.1, ex + ew, eye_y + eh * 0.6)
            P.ink(ctx, 3)
            ctx.stroke()
    # Augenbrauen
    bc = P.shade(L["hair"], 0.5) if L.get("hair_style") != "bald" else P.shade(L["skin"], 0.5)
    brows = {
        "neutral": (0, 0), "happy": (-4, 0.05), "angry": (8, -0.35), "scared": (-12, 0.35),
        "surprised": (-16, 0), "suspicious": (0, -0.2), "sad": (-6, 0.35), "smirk": (-2, -0.1),
        "creepy": (-6, -0.2),
    }.get(expr, (0, 0))
    for side in (-1, 1):
        dy, tilt = brows
        if expr in ("suspicious", "smirk") and side == 1:
            dy, tilt = -10, 0.15
        bx, by = side * 24, eye_y - 28 + dy
        x0, x1 = bx - 15, bx + 15
        y_in = by - tilt * 14
        y_out = by + tilt * 14
        pts = [(x0, y_out), (x1, y_in)] if side == -1 else [(x0, y_in), (x1, y_out)]
        P.line(ctx, pts, 7, bc)
    # Nase
    ctx.move_to(-2, c + 4)
    ctx.curve_to(-10, c + 22, -6, c + 26, 6, c + 24)
    P.ink(ctx, 3.5)
    ctx.stroke()
    # Falten (Alter)
    if L.get("age") == "old":
        for side in (-1, 1):
            P.line(ctx, [(side * 44, c - 2), (side * 50, c + 4)], 2.5)
            P.line(ctx, [(side * 16, c + 34), (side * 22, c + 44)], 2.5)
    if L.get("mustache"):
        P.blob(ctx, [(-26, c + 34), (0, c + 28), (26, c + 34), (14, c + 40), (0, c + 36), (-14, c + 40)],
               P.shade(L["hair"], 0.8), 3)
    if L.get("beard"):
        P.blob(ctx, [(-HX + 6, c + 10), (-40, c + 60), (0, c + HY + 12), (40, c + 60), (HX - 6, c + 10),
                     (30, c + 50), (0, c + 58), (-30, c + 50)], L["hair"], 4)
    _mouth(ctx, expr, mouth, c + 44, L)
    if expr == "happy":
        for side in (-1, 1):
            P.ellipse(ctx, side * 42, c + 26, 10, 6, "#e88a8a", 0, alpha=0.5)


def _mouth(ctx, expr, m, y, L):
    w = {"surprised": 14, "scared": 22, "happy": 26, "creepy": 34, "smirk": 22}.get(expr, 20)
    if m > 0.12:
        h = 6 + m * 20
        if expr in ("surprised",):
            h += 8
        top = y - h * 0.35
        ctx.move_to(-w, y - 2)
        ctx.curve_to(-w, top, w, top, w, y - 2)
        ctx.curve_to(w, y + h, -w, y + h, -w, y - 2)
        ctx.close_path()
        P.fill_stroke(ctx, "#5c1f22", 4)
        if h > 14:
            P.ellipse(ctx, 0, y + h * 0.55, w * 0.55, h * 0.22, "#d86b72", 0)
        return
    curve = {"happy": 10, "sad": -9, "angry": -6, "scared": -5, "creepy": 14, "smirk": 6,
             "suspicious": -2}.get(expr, 2)
    if expr == "creepy":
        ctx.move_to(-w, y - 6)
        ctx.curve_to(-w / 2, y + curve, w / 2, y + curve, w, y - 6)
        ctx.curve_to(w / 2, y + curve - 8, -w / 2, y + curve - 8, -w, y - 6)
        P.fill_stroke(ctx, "#f4f1e6", 3.5)
        for i in range(-3, 4):
            P.line(ctx, [(i * 9, y + 1), (i * 9, y + 8)], 2)
        return
    if expr == "smirk":
        ctx.move_to(-w * 0.8, y + 2)
        ctx.curve_to(0, y + 4, w * 0.6, y + 2, w, y - curve)
    else:
        ctx.move_to(-w, y)
        ctx.curve_to(-w / 2, y + curve, w / 2, y + curve, w, y)
    P.ink(ctx, 4.5)
    ctx.stroke()


def _hair_front(ctx, L, style, hair, c):
    top = c - HY
    if style in ("bald",):
        P.blob(ctx, [(-HX - 2, c - 10), (-HX + 8, c - 40), (-HX + 16, c - 8)], hair, 3)
        P.blob(ctx, [(HX + 2, c - 10), (HX - 8, c - 40), (HX - 16, c - 8)], hair, 3)
        return
    if style == "cap":
        col = L.get("accent", "#2f4f8f")
        P.blob(ctx, [(-HX - 4, c - 34), (-HX + 4, top + 6), (0, top - 14), (HX - 4, top + 6), (HX + 4, c - 34),
                     (0, c - 42)], col)
        P.ellipse(ctx, 0, c - 42, HX + 24, 11, P.shade(col, 0.8))
        P.ellipse(ctx, 0, top + 2, 7, 5, P.shade(col, 0.7), 3)
        for side in (-1, 1):
            P.blob(ctx, [(side * (HX + 2), c - 14), (side * (HX - 4), c + 18), (side * (HX - 14), c - 8)], hair, 3)
        return
    if style == "beanie":
        col = L.get("accent", "#6b4a35")
        P.blob(ctx, [(-HX - 6, c - 20), (-HX + 2, top + 2), (0, top - 22), (HX - 2, top + 2), (HX + 6, c - 20)], col)
        P.rrect(ctx, -HX - 8, c - 42, 2 * HX + 16, 30, 12, P.shade(col, 0.85))
        return
    if style == "curly":
        pts = []
        for i in range(13):
            a = math.pi + i * math.pi / 12
            r = HX + 14 + (8 if i % 2 else 0)
            pts.append((math.cos(a) * r, c - 18 + math.sin(a) * (HY + 6) * 0.92 + (6 if i % 2 else 0)))
        pts += [(HX - 10, c - 30), (0, c - 46), (-HX + 10, c - 30)]
        P.blob(ctx, pts, hair)
        return
    # short / long / bun / ponytail: Haarkappe mit Scheitel
    fringe = {"short": c - 54, "long": c - 50, "bun": c - 56, "ponytail": c - 54}.get(style, c - 54)
    pts = [(-HX - 3, c + (10 if style == "long" else -4)), (-HX - 2, c - 40), (-HX + 14, top + 6),
           (0, top - 8), (HX - 14, top + 6), (HX + 2, c - 40), (HX + 3, c + (10 if style == "long" else -4)),
           (HX - 8, c - 34), (HX - 20, fringe + 4), (16, fringe), (-20, fringe + 6), (-HX + 8, c - 34)]
    if style == "short":
        pts[3] = (-6, top - 14)
        pts.insert(4, (12, top - 4))
        pts.insert(5, (26, top - 12))
    P.blob(ctx, pts, hair)
    P.line(ctx, [(10, top + 2), (22, fringe + 2)], 3, P.shade(hair, 0.6))
