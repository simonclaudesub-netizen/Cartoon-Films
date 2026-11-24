"""Detaillierte Cartoon-Kulissen in Zentralperspektive (POV).

Jede Kulisse liefert:
  back(ctx)            statische Ebene (wird pro Einstellung einmal gerendert und gecacht)
  dynamic(ctx, t)      bewegte Hintergrund-Details (Wolken, Lichtspalt, ...)
  front(ctx)           Vordergrund vor den Figuren (optional)
  emissive(ctx, t)     Leuchtende Elemente, die nach der Nacht-Färbung gezeichnet werden
  spots                benannte Positionen für Figuren: name -> (x, z) in Metern
  night, lights        Lichtstimmung
"""
import math
import random

from . import prims as P
from .persp import Cam, W, H


def room(ctx, cam, xl, xr, yc, yf, zb, wall, floor, ceil, side=None, zn=0.2):
    side = side or P.shade(wall, 0.9)
    cam.quad(ctx, [(xl, yc, zn), (xr, yc, zn), (xr, yc, zb), (xl, yc, zb)], ceil)
    cam.quad(ctx, [(xl, yf, zn), (xr, yf, zn), (xr, yf, zb), (xl, yf, zb)], floor)
    cam.quad(ctx, [(xl, yc, zn), (xl, yc, zb), (xl, yf, zb), (xl, yf, zn)], side)
    cam.quad(ctx, [(xr, yc, zn), (xr, yc, zb), (xr, yf, zb), (xr, yf, zn)], side)
    cam.quad(ctx, [(xl, yc, zb), (xr, yc, zb), (xr, yf, zb), (xl, yf, zb)], wall)


def baseboard(ctx, cam, xl, xr, yf, zb, color, h=0.1, zn=0.2):
    cam.quad(ctx, [(xl, yf - h, zn), (xl, yf - h, zb), (xl, yf, zb), (xl, yf, zn)], color, 3)
    cam.quad(ctx, [(xr, yf - h, zn), (xr, yf - h, zb), (xr, yf, zb), (xr, yf, zn)], color, 3)
    cam.quad(ctx, [(xl, yf - h, zb), (xr, yf - h, zb), (xr, yf, zb), (xl, yf, zb)], color, 3)


def floor_planks(ctx, cam, xl, xr, yf, zb, n=10, color=(0, 0, 0), alpha=0.25, zn=0.3):
    for i in range(1, n):
        x = xl + (xr - xl) * i / n
        a, b = cam.p(x, yf, zn), cam.p(x, yf, zb)
        ctx.move_to(*a)
        ctx.line_to(*b)
        ctx.set_source_rgba(*color, alpha)
        ctx.set_line_width(3)
        ctx.stroke()


def floor_tiles(ctx, cam, xl, xr, yf, zb, step=0.4, zn=0.3, alpha=0.3):
    floor_planks(ctx, cam, xl, xr, yf, zb, int((xr - xl) / step), alpha=alpha, zn=zn)
    z = zn
    while z < zb:
        a, b = cam.p(xl, yf, z), cam.p(xr, yf, z)
        ctx.move_to(*a)
        ctx.line_to(*b)
        ctx.set_source_rgba(0, 0, 0, alpha)
        ctx.set_line_width(3)
        ctx.stroke()
        z += step


def wall_rect(ctx, cam, x0, x1, y0, y1, z, color, lw=P.LW):
    cam.quad(ctx, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], color, lw)


def side_rect(ctx, cam, x, z0, z1, y0, y1, color, lw=P.LW):
    cam.quad(ctx, [(x, y0, z0), (x, y0, z1), (x, y1, z1), (x, y1, z0)], color, lw)


def door(ctx, cam, x0, x1, ytop, yf, z, color, peephole=True, handle_side=1, frame="#e9e6dc", number=None):
    wall_rect(ctx, cam, x0 - 0.07, x1 + 0.07, ytop - 0.07, yf, z, frame)
    wall_rect(ctx, cam, x0, x1, ytop, yf, z, color)
    # Füllungen
    for (a, b) in ((ytop + 0.12, ytop + 0.85), (ytop + 1.05, yf - 0.15)):
        wall_rect(ctx, cam, x0 + 0.12, x1 - 0.12, a, b, z, P.shade(color, 0.92), 3)
    hx = x1 - 0.1 if handle_side > 0 else x0 + 0.1
    hy = ytop + 1.0
    a, b = cam.p(hx - 0.04 * handle_side, hy - 0.06, z), cam.p(hx + 0.0, hy + 0.12, z)
    P.rrect(ctx, min(a[0], b[0]) - 4, a[1], abs(b[0] - a[0]) + 8, b[1] - a[1], 4, "#bfbfc6", 3)
    pa = cam.p(hx - 0.13 * handle_side, hy, z)
    pb = cam.p(hx, hy, z)
    P.line(ctx, [pa, pb], cam.scale(z) * 0.035)
    P.line(ctx, [pa, pb], cam.scale(z) * 0.022, "#d6d6dc")
    if peephole:
        c = cam.p((x0 + x1) / 2, ytop + 0.5, z)
        P.ellipse(ctx, c[0], c[1], cam.scale(z) * 0.02, cam.scale(z) * 0.02, "#30303a", 3)
    if number:
        c = cam.p((x0 + x1) / 2, ytop + 0.3, z)
        sz = cam.scale(z) * 0.09
        P.rrect(ctx, c[0] - sz * 0.9, c[1] - sz * 0.75, sz * 1.8, sz * 1.0, 4, "#d9c27a", 3)
        P.text(ctx, number, c[0], c[1] + sz * 0.1, sz * 0.75, family="Comic Neue", color="#3a3020")


class Set:
    name = "set"
    night = False
    tint = (0.30, 0.34, 0.55)
    lights = []
    peephole = False
    spots = {}

    def __init__(self, time="day", variant=None):
        self.time = time
        self.night = time == "night"
        self.variant = variant
        self.cam = Cam()

    def has(self, v):
        """Varianten lassen sich kombinieren, z. B. "flicker+slippers"."""
        return v in (self.variant or "").split("+")

    def back(self, ctx):
        pass

    def dynamic(self, ctx, t):
        pass

    def front(self, ctx):
        pass

    def emissive(self, ctx, t):
        pass

    def light_level(self, t):
        return 1.0


# ---------------------------------------------------------------------------
class Flur(Set):
    """Eigener Wohnungsflur, Blick auf die Wohnungstür (4B von innen)."""
    name = "flur"
    spots = {"tuer": (0.0, 3.2)}

    def back(self, ctx):
        c = self.cam
        xl, xr, yc, yf, zb = -0.8, 0.8, -0.95, 1.6, 3.4
        room(ctx, c, xl, xr, yc, yf, zb, "#e7e1d3", "#9a7350", "#efece4", side="#ddd5c4")
        floor_planks(ctx, c, xl, xr, yf, zb, 7)
        baseboard(ctx, c, xl, xr, yf, zb, "#f4f1ea")
        P.stains(ctx, 0, 0, W, 500, "#8c8577", 14, 3, alpha=0.12)
        door(ctx, c, -0.46, 0.46, -0.5, yf, zb - 0.001, "#8b6b4c", number=None)
        # Sicherheitskette
        a = c.p(0.32, 0.2, zb - 0.01)
        b = c.p(0.12, 0.28, zb - 0.01)
        P.rrect(ctx, a[0] - 8, a[1] - 12, 16, 24, 3, "#bfbfc6", 3)
        ctx.move_to(*a)
        ctx.curve_to(a[0] - 20, a[1] + 40, b[0] + 10, b[1] + 30, b[0], b[1])
        P.ink(ctx, 4)
        ctx.stroke()
        # Garderobe links
        side_rect(ctx, c, xl + 0.001, 1.3, 2.4, -0.05, 0.0, "#6d5039", 3)
        rr = random.Random(5)
        for i, z in enumerate((1.45, 1.8, 2.15)):
            col = ["#5a6e8a", "#8a3d3d", "#3f5e4a"][i]
            top = c.p(xl, 0.0, z)
            bot = c.p(xl, 0.75 + rr.uniform(0, 0.15), z)
            w = c.scale(z) * 0.16
            P.blob(ctx, [(top[0] - 4, top[1]), (top[0] + w, top[1] + w * 0.4), (top[0] + w * 1.1, bot[1]),
                         (top[0] + 2, bot[1] + 8)], col)
        # Schuhregal rechts
        c.box(ctx, 0.52, 0.8, 1.2, 1.6, 1.4, 2.2, "#c9c1ae")
        for z in (1.6, 1.95):
            a = c.p(0.55, 1.18, z)
            P.ellipse(ctx, a[0], a[1], c.scale(z) * 0.08, c.scale(z) * 0.03, "#2e2e33", 3)
        # Bild rechts
        side_rect(ctx, c, xr - 0.001, 1.0, 1.6, -0.45, 0.05, "#f3efe2", 4)
        side_rect(ctx, c, xr - 0.002, 1.08, 1.52, -0.38, -0.02, "#7fa7c4", 3)
        # Lichtschalter
        side_rect(ctx, c, xr - 0.001, 2.75, 2.85, 0.1, 0.2, "#fbfaf6", 3)
        # Deckenlampe (aus)
        a = c.p(0, yc, 2.0)
        P.line(ctx, [a, (a[0], a[1] + 40)], 3)
        P.ellipse(ctx, a[0], a[1] + 55, 34, 22, "#f2f0e6")
        if self.has("note") or self.has("photoback") or self.has("photoback2"):
            # Zettel (bzw. Foto-Rückseite), unter der Tür durchgeschoben (liegt auf dem Boden)
            pts = [c.p(x, yf, z) for x, z in ((-0.27, 2.5), (0.27, 2.58), (0.23, 3.08), (-0.29, 3.0))]
            P.poly(ctx, [(p[0] + 6, p[1] + 6) for p in pts], "#000000", lw=0, alpha=0.18)
            P.poly(ctx, pts, "#fbf7e8" if self.has("note") else "#efe4c8", 4)
            cx = sum(p[0] for p in pts) / 4
            cy = sum(p[1] for p in pts) / 4
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(1.0, 0.42)
            ctx.rotate(0.06)
            if self.has("note"):
                P.text(ctx, "Gut gemacht.", -6, 8, 36, color="#2b2b33")
                P.text(ctx, "– O.", 60, 62, 36, color="#2b2b33")
            else:
                word = "Nicht öffnen." if self.has("photoback") else "Nicht wegwerfen."
                P.text(ctx, word, -6, -30, 34, color="#2b2b33")
                P.text(ctx, word, -6, 22, 34, color="#2b2b33")
                P.text(ctx, "– O.", 70, 76, 34, color="#2b2b33")
            ctx.restore()
        if self.has("photo") or self.has("photo2"):
            # Altes Foto (Vorderseite) auf dem Boden: junger Mann vor einer Tür „4B“, sepia
            pts = [c.p(x, yf, z) for x, z in ((-0.27, 2.5), (0.27, 2.58), (0.23, 3.08), (-0.29, 3.0))]
            P.poly(ctx, [(p[0] + 6, p[1] + 6) for p in pts], "#000000", lw=0, alpha=0.18)
            P.poly(ctx, pts, "#f6f1e4", 4)
            inner = [c.p(x, yf, z) for x, z in ((-0.23, 2.55), (0.23, 2.62), (0.2, 2.98), (-0.25, 2.92))]
            P.poly(ctx, inner, "#a8875e", 2)
            cx = sum(p[0] for p in inner) / 4
            cy = sum(p[1] for p in inner) / 4
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(1.0, 0.42)
            ctx.rotate(0.06)
            P.rrect(ctx, 30, -120, 120, 230, 6, "#7a5c3c", 3)       # Tür
            P.text(ctx, "4B", 70, -70, 30, color="#e9d9b4")
            P.ellipse(ctx, -50, -60, 26, 30, "#4a3624")              # Kopf (Silhouette)
            P.rrect(ctx, -90, -30, 80, 140, 18, "#4a3624", 0)        # Körper
            if self.has("photo2"):
                # zweite Person: im senfgelben Kapuzenpulli der Hauptfigur
                P.ellipse(ctx, -150, -55, 24, 28, "#4a3624")
                P.rrect(ctx, -188, -26, 76, 136, 18, "#c9a23a", 0)
            P.text(ctx, "1983", -185 if self.has("photo2") else -150, -110 if self.has("photo2") else 95, 26,
                   color="#3b2c1c")
            ctx.restore()

    def dynamic(self, ctx, t):
        pass

    def emissive(self, ctx, t):
        if not self.night:
            return
        c = self.cam
        zb = 3.399
        a, b = c.p(-0.44, 1.585, zb), c.p(0.44, 1.6, zb)
        ctx.rectangle(a[0], a[1] - 3, b[0] - a[0], b[1] - a[1] + 4)
        P.set_col(ctx, "#ffd77a")
        ctx.fill()
        if self.has("feet"):
            # Schatten von zwei Füßen im Lichtspalt
            sway = math.sin(t * 1.7) * 6
            for dx in (-38, 30):
                P.set_col(ctx, "#141418")
                ctx.rectangle((a[0] + b[0]) / 2 + dx + sway - 22, a[1] - 3, 44, b[1] - a[1] + 4)
                ctx.fill()

    lights = [((540, 1160), 420, (1.0, 0.8, 0.45), 0.35)]


# ---------------------------------------------------------------------------
class Wohnzimmer(Set):
    """Neue, leere Wohnung mit Umzugskartons."""
    name = "wohnzimmer"
    spots = {"mitte": (-0.25, 3.0), "links": (-0.9, 3.4), "rechts": (0.7, 3.2), "nah": (-0.15, 2.0)}

    def back(self, ctx):
        c = self.cam
        xl, xr, yc, yf, zb = -2.3, 2.3, -1.05, 1.6, 5.0
        room(ctx, c, xl, xr, yc, yf, zb, "#ece6d6", "#b58a5c", "#f4f1ea", side="#e2dac6")
        floor_planks(ctx, c, xl, xr, yf, zb, 14)
        baseboard(ctx, c, xl, xr, yf, zb, "#f6f3ec")
        P.stains(ctx, -100, -100, W + 100, 700, "#8c8577", 18, 7, alpha=0.1)
        # Fenster rechts an der Rückwand
        self.win = (0.35, 1.85, -0.55, 0.65, zb - 0.001)
        x0, x1, y0, y1, z = self.win
        wall_rect(ctx, c, x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 + 0.06, z, "#fbfaf6")
        wall_rect(ctx, c, x0, x1, y0, y1, z, "#8fc3ea")
        # Häuser gegenüber
        for i, (hx0, hx1, hy, col) in enumerate([(0.35, 0.9, -0.1, "#d99b74"), (0.9, 1.45, -0.35, "#c9c3a4"),
                                                 (1.45, 1.85, 0.0, "#a8b8c8")]):
            wall_rect(ctx, c, hx0, hx1, hy, y1, z, col, 3)
            for wx in range(2):
                for wy in range(3):
                    xx = hx0 + 0.08 + wx * (hx1 - hx0 - 0.1) / 2
                    yy = hy + 0.08 + wy * 0.22
                    if yy + 0.12 < y1:
                        wall_rect(ctx, c, xx, xx + 0.12, yy, yy + 0.12, z, "#56708c", 2.5)
        # Fensterkreuz
        mx = (x0 + x1) / 2
        P.line(ctx, [c.p(mx, y0, z), c.p(mx, y1, z)], 10)
        P.line(ctx, [c.p(mx, y0, z), c.p(mx, y1, z)], 5, "#fbfaf6")
        # Heizkörper
        wall_rect(ctx, c, x0 + 0.1, x1 - 0.1, y1 + 0.15, y1 + 0.55, z, "#f4f2ec", 4)
        for i in range(12):
            xx = x0 + 0.15 + i * (x1 - x0 - 0.3) / 11
            P.line(ctx, [c.p(xx, y1 + 0.18, z), c.p(xx, y1 + 0.52, z)], 2.5)
        # Offene Tür links (dunkler Flur dahinter)
        wall_rect(ctx, c, -1.75, -0.75, -0.55, yf, zb - 0.001, "#e9e6dc")
        wall_rect(ctx, c, -1.68, -0.82, -0.48, yf, zb - 0.002, "#5d5649")
        cam_door = [c.p(-1.68, -0.48, zb), c.p(-1.3, -0.4, zb - 0.6), c.p(-1.3, yf, zb - 0.6), c.p(-1.68, yf, zb)]
        P.poly(ctx, cam_door, "#f2efe6")
        # Nagellöcher / helle Flecken von alten Bildern
        for (x, y) in ((-0.3, -0.3), (-0.1, -0.2), (-2.0, -0.2)):
            if x > xl:
                wall_rect(ctx, c, x, x + 0.35, y, y + 0.28, zb - 0.001, "#f5f1e6", 0)
                a = c.p(x + 0.175, y - 0.02, zb)
                P.ellipse(ctx, a[0], a[1], 3, 3, "#333333", 0)
        # Glühbirne
        a = c.p(0, yc, 2.6)
        P.line(ctx, [a, (a[0], a[1] + 110)], 3)
        P.ellipse(ctx, a[0], a[1] + 128, 16, 20, "#fff4c2", 4)

    def front(self, ctx):
        c = self.cam
        boxes = [(-2.1, -1.35, 1.0, 1.6, 1.6, 2.3, "KÜCHE"), (-2.05, -1.45, 0.45, 1.0, 1.7, 2.25, "BÜCHER"),
                 (1.15, 2.0, 1.05, 1.6, 1.9, 2.6, "BAD"), (1.35, 2.0, 0.6, 1.05, 2.0, 2.5, None),
                 (-1.2, -0.7, 1.25, 1.6, 3.6, 4.0, None)]
        for (x0, x1, y0, y1, z0, z1, label) in boxes:
            c.box(ctx, x0, x1, y0, y1, z0, z1, "#c9a26b", top="#dcb882", side="#a9844f")
            m = (x0 + x1) / 2
            c.quad(ctx, [(m - 0.06, y0, z0), (m + 0.06, y0, z0), (m + 0.06, y0, z1), (m - 0.06, y0, z1)], "#e9d6a6", 2)
            if label:
                p = c.p(m, (y0 + y1) / 2 + 0.05, z0)
                P.text(ctx, label, p[0], p[1], c.scale(z0) * 0.11, family="Comic Neue", color="#2a2a2a")

    def dynamic(self, ctx, t):
        c = self.cam
        x0, x1, y0, y1, z = self.win
        a, b = c.p(x0, y0, z), c.p(x1, y1, z)
        ctx.save()
        ctx.rectangle(a[0] + 3, a[1] + 3, b[0] - a[0] - 6, (c.p(0, -0.12, z)[1]) - a[1])
        ctx.clip()
        for i, (ox, oy, sc) in enumerate(((0, 0, 1.0), (260, 30, 0.8), (520, -10, 1.1))):
            cx = a[0] - 120 + (ox + t * 14) % (b[0] - a[0] + 240)
            cy = a[1] + 40 + oy
            P.blob(ctx, [(cx - 50 * sc, cy + 10), (cx - 30 * sc, cy - 18), (cx, cy - 26 * sc),
                         (cx + 34 * sc, cy - 14), (cx + 52 * sc, cy + 10)], "#ffffff", 3)
        ctx.restore()


# ---------------------------------------------------------------------------
class Treppenhaus(Set):
    """Treppenhaus-Absatz im 4. Stock, Blick auf Wohnung 4A gegenüber."""
    name = "treppenhaus"
    spots = {"tuer": (0.0, 3.25), "mitte": (0.0, 2.4), "nah": (0.0, 1.35), "links": (-0.8, 2.6)}

    def back(self, ctx):
        c = self.cam
        xl, xr, yc, yf, zb = -1.5, 1.6, -1.15, 1.6, 3.6
        room(ctx, c, xl, xr, yc, yf, zb, "#ece7d8", "#c9c2b0", "#f1eee6", side="#e3ddcc")
        floor_tiles(ctx, c, xl, xr, yf, zb, 0.45)
        # Zweifarbige Treppenhaus-Wand (Ölsockel)
        ysock = 0.45
        c.quad(ctx, [(xl, ysock, 0.2), (xl, ysock, zb), (xl, yf, zb), (xl, yf, 0.2)], "#93a796")
        c.quad(ctx, [(xl, ysock, zb), (xr, ysock, zb), (xr, yf, zb), (xl, yf, zb)], "#9db09f")
        P.line(ctx, [c.p(xl, ysock, 0.2), c.p(xl, ysock, zb), c.p(xr, ysock, zb)], 6, "#6e8472")
        P.stains(ctx, -200, 300, W + 200, 1500, "#5d5a50", 30, 11, alpha=0.1)
        # Tür 4A
        door(ctx, c, -0.48, 0.48, -0.55, yf, zb - 0.001, "#f1eee4", number="4A", frame="#d8d3c4")
        if self.has("open"):
            wall_rect(ctx, c, -0.48, 0.48, -0.55, yf, zb - 0.002, "#d9a865")
            wall_rect(ctx, c, -0.3, 0.1, -0.2, 0.3, zb - 0.003, "#b77a4a", 3)  # Bild im Flur
            P.poly(ctx, [c.p(-0.48, -0.55, zb), c.p(-0.75, -0.6, zb - 0.6), c.p(-0.75, yf, zb - 0.6),
                         c.p(-0.48, yf, zb)], "#f1eee4")
        # Namensschild + Klingel
        wall_rect(ctx, c, 0.62, 0.8, 0.05, 0.25, zb - 0.001, "#e7d9a8", 3)
        a = c.p(0.71, 0.12, zb)
        P.text(ctx, "BRANDT", a[0], a[1], c.scale(zb) * 0.04, family="Comic Neue", color="#333333")
        a = c.p(0.71, 0.2, zb)
        P.ellipse(ctx, a[0], a[1] + 4, 6, 6, "#ffffff", 3)
        # Fußmatte
        c.quad(ctx, [(-0.4, yf, zb - 0.6), (0.4, yf, zb - 0.6), (0.4, yf, zb - 0.05), (-0.4, yf, zb - 0.05)], "#8a5a3a", 4)
        for i in range(1, 4):
            z = zb - 0.6 + i * 0.14
            P.line(ctx, [c.p(-0.35, yf, z), c.p(0.35, yf, z)], 3, "#6d4329")
        if self.has("slippers"):
            # Frau Brandts Hausschuhe, ordentlich nebeneinander auf der Matte
            for x0 in (-0.2, 0.04):
                pts = [c.p(x, yf, z) for x, z in ((x0, zb - 0.42), (x0 + 0.14, zb - 0.42), (x0 + 0.13, zb - 0.12),
                                                  (x0 + 0.01, zb - 0.12))]
                P.blob(ctx, pts, "#c25b7a", 4)
                a1, b1 = c.p(x0 + 0.01, yf - 0.03, zb - 0.38), c.p(x0 + 0.13, yf - 0.03, zb - 0.38)
                P.blob(ctx, [a1, ((a1[0] + b1[0]) / 2, a1[1] - 14), b1, ((a1[0] + b1[0]) / 2, a1[1] + 8)], "#f2e3ea", 3)
        # Pflanze links neben der Tür
        c.box(ctx, -1.0, -0.75, 1.3, 1.6, 3.2, 3.45, "#b7653e")
        base = c.p(-0.875, 1.3, 3.3)
        rr = random.Random(2)
        for i in range(7):
            ang = -math.pi / 2 + rr.uniform(-1.0, 1.0)
            ln = rr.uniform(90, 150)
            tip = (base[0] + math.cos(ang) * ln * 0.6, base[1] + math.sin(ang) * ln)
            P.blob(ctx, [base, ((base[0] + tip[0]) / 2 - 14, (base[1] + tip[1]) / 2), tip,
                         ((base[0] + tip[0]) / 2 + 14, (base[1] + tip[1]) / 2)], "#4f8a4a", 3)
        # Wandlampe links
        side_rect(ctx, c, xl + 0.001, 2.2, 2.5, -0.55, -0.35, "#f6efc9", 4)
        # Schwarzes Brett (Hausordnung)
        side_rect(ctx, c, xl + 0.001, 1.0, 1.7, -0.3, 0.25, "#a77b4f", 4)
        for i, (z0, y0) in enumerate(((1.05, -0.25), (1.3, -0.2), (1.45, 0.0))):
            side_rect(ctx, c, xl + 0.002, z0, z0 + 0.2, y0, y0 + 0.2, "#fbf8ee", 2.5)
        a = c.p(xl, -0.12, 1.15)
        # Treppengeländer rechts
        rail_x = 1.35
        for i in range(9):
            z = 0.9 + i * 0.3
            P.line(ctx, [c.p(rail_x, 0.65, z), c.p(rail_x, yf, z)], c.scale(z) * 0.03)
            P.line(ctx, [c.p(rail_x, 0.65, z), c.p(rail_x, yf, z)], c.scale(z) * 0.018, "#5d4a3a")
        c.quad(ctx, [(rail_x - 0.04, 0.6, 0.9), (rail_x + 0.04, 0.6, 0.9), (rail_x + 0.04, 0.6, zb),
                     (rail_x - 0.04, 0.6, zb)], "#7a5a3c", 4)

    lights = [((140, 640), 520, (1.0, 0.85, 0.55), 0.45), ((540, 700), 700, (0.9, 0.85, 0.6), 0.2)]

    def light_level(self, t):
        if self.has("flicker"):
            f = 1.0
            for k, (t0, d) in enumerate(((1.1, 0.12), (2.4, 0.08), (2.6, 0.2))):
                if t0 <= t % 4.0 < t0 + d:
                    f = 0.35
            return f
        return 1.0

    def emissive(self, ctx, t):
        if self.night:
            c = self.cam
            a, b = c.p(-1.5, -0.55, 2.2), c.p(-1.5, -0.35, 2.5)
            P.ellipse(ctx, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 22, 34, "#fff3c0", 0,
                      alpha=0.9 * self.light_level(t))


# ---------------------------------------------------------------------------
class Schlafzimmer(Set):
    """Schlafzimmer bei Nacht (Hintergrund für Handy-Szenen)."""
    name = "schlafzimmer"
    spots = {"mitte": (0.0, 3.0)}

    def back(self, ctx):
        c = self.cam
        c.eye = 1.0
        xl, xr, yc, yf, zb = -2.0, 2.0, -1.6, 1.0, 4.0
        room(ctx, c, xl, xr, yc, yf, zb, "#c9d3df", "#8a6a4f", "#e6e9ee", side="#b8c3d1")
        floor_planks(ctx, c, xl, xr, yf, zb, 10)
        wall_rect(ctx, c, -0.6, 0.6, -0.9, 0.0, zb - 0.001, "#f4f4f4")
        wall_rect(ctx, c, -0.54, 0.54, -0.84, -0.06, zb - 0.002, "#1d2a4a")
        m = c.p(0.25, -0.6, zb)
        P.ellipse(ctx, m[0], m[1], 26, 26, "#f6f0cf", 3)
        P.line(ctx, [c.p(0, -0.9, zb), c.p(0, 0.0, zb)], 6, "#f4f4f4")
        # Schrank links
        c.box(ctx, -2.0, -1.3, -0.9, 1.0, 2.3, 3.5, "#a07a55")
        # Bettdecke im Vordergrund
        P.blob(ctx, [(-200, 1500), (200, 1380), (540, 1420), (880, 1370), (1280, 1480), (1280, 2300), (-200, 2300)],
               "#5b7fa8")
        P.blob(ctx, [(100, 1600), (400, 1540), (700, 1580), (650, 1640), (300, 1660)], "#4d6f96", 0)

    lights = [((620, 600), 380, (0.7, 0.8, 1.0), 0.3)]


# ---------------------------------------------------------------------------
class Keller(Set):
    """Kellergang mit Holzlatten-Abteilen; am Ende Abteil 4B mit neuem Schloss.
    Variante "flashlight": nur der Lichtkegel der Handy-Taschenlampe."""
    name = "keller"
    tint = (0.16, 0.17, 0.26)
    spots = {"abteil": (0.0, 3.55), "mitte": (0.0, 2.5), "nah": (0.0, 1.45), "links": (-0.55, 2.7)}

    def back(self, ctx):
        c = self.cam
        xl, xr, yc, yf, zb = -0.95, 0.95, -0.85, 1.6, 4.2
        room(ctx, c, xl, xr, yc, yf, zb, "#9a978e", "#7d7a72", "#a9a69d", side="#8f8c83")
        floor_tiles(ctx, c, xl, xr, yf, zb, 0.6, alpha=0.18)
        P.stains(ctx, -100, 200, W + 100, 1700, "#4b4840", 40, 21, alpha=0.16)
        # Stromkabel an der Decke (dünn, perspektivisch)
        P.line(ctx, [c.p(-0.7, yc + 0.03, 1.6), c.p(-0.7, yc + 0.03, zb)], 3, "#3a3a3a")
        P.line(ctx, [c.p(0.72, yc + 0.03, 1.6), c.p(0.72, yc + 0.03, zb)], 3, "#3a3a3a")
        # Seitliche Abteile (Holzlatten)
        for side in (-1, 1):
            x = xl + 0.001 if side < 0 else xr - 0.001
            for i, (z0, z1) in enumerate(((0.9, 1.7), (1.85, 2.65), (2.8, 3.6))):
                side_rect(ctx, c, x, z0, z1, -0.6, yf - 0.05, "#8a6a47", 4)
                for k in range(1, 7):
                    z = z0 + (z1 - z0) * k / 7
                    P.line(ctx, [c.p(x, -0.6, z), c.p(x, yf - 0.05, z)], 3, "#4a3727")
                num = ["2A", "3B", "1A", "2B", "3A", "1B"][i * 2 + (side > 0)]
                a = c.p(x, -0.45, (z0 + z1) / 2)
                P.rrect(ctx, a[0] - 26, a[1] - 18, 52, 34, 4, "#e9e2c8", 3)
                P.text(ctx, num, a[0], a[1] + 9, 24, family="Comic Neue", color="#333333")
        # Abteil 4B am Ende: Lattentür mit Nummer und glänzendem neuem Vorhängeschloss
        wall_rect(ctx, c, -0.5, 0.5, -0.6, yf, zb - 0.001, "#8a6a47")
        for k in range(1, 9):
            x = -0.5 + k / 9
            P.line(ctx, [c.p(x, -0.6, zb), c.p(x, yf, zb)], 4, "#4a3727")
        wall_rect(ctx, c, -0.5, 0.5, 0.35, 0.45, zb - 0.002, "#6d5236", 3)
        a = c.p(0.0, -0.4, zb)
        P.rrect(ctx, a[0] - 44, a[1] - 26, 88, 50, 6, "#f3ecd2", 4)
        P.text(ctx, "4B", a[0], a[1] + 14, 38, family="Comic Neue", color="#7a1f1f")
        lk = c.p(0.3, 0.32, zb)
        m = c.scale(zb)  # Pixel pro Meter in der Tiefe der Abteiltür
        ctx.save()
        ctx.translate(*lk)
        ctx.arc(0, -0.035 * m, 0.028 * m, math.pi, 0)
        P.ink(ctx, max(3, 0.012 * m))
        ctx.stroke()
        P.rrect(ctx, -0.04 * m, -0.035 * m, 0.08 * m, 0.07 * m, 4, "#e8c95a", 3)
        P.ellipse(ctx, 0, -0.005 * m, 0.008 * m, 0.012 * m, "#3a3020", 0)
        P.line(ctx, [(-0.028 * m, -0.025 * m), (-0.008 * m, -0.03 * m)], 2.5, "#fff7cf")
        ctx.restore()
        # Glühbirne
        a = c.p(0, yc, 2.2)
        P.line(ctx, [a, (a[0], a[1] + 50)], 3)
        P.ellipse(ctx, a[0], a[1] + 66, 18, 22, "#f4efd6", 3)

    def light_level(self, t):
        return 1.0

    lights = [((540, 980), 480, (1.0, 0.93, 0.75), 0.38), ((540, 1000), 220, (1.0, 0.96, 0.85), 0.2)]

    def emissive(self, ctx, t):
        if self.night and not self.has("flashlight"):
            c = self.cam
            a = c.p(0, -0.85, 2.2)
            P.ellipse(ctx, a[0], a[1] + 66, 18, 22, "#fff3c0", 0, alpha=0.85)


SETS = {"flur": Flur, "wohnzimmer": Wohnzimmer, "treppenhaus": Treppenhaus, "schlafzimmer": Schlafzimmer, "keller": Keller}


def make(name, time="day", variant=None):
    return SETS[name](time=time, variant=variant)
