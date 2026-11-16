"""Einfache Lochkamera-Perspektive für POV-Räume.

3D-Koordinaten in Metern: X nach rechts, Y nach unten, Z in die Tiefe.
Die Kamera (das Auge des Zuschauers) sitzt im Ursprung.
"""
from . import prims as P

W, H = 1080, 1920


class Cam:
    def __init__(self, f=620.0, cx=W / 2, cy=860.0, eye=1.6):
        self.f, self.cx, self.cy, self.eye = f, cx, cy, eye

    def p(self, x, y, z):
        z = max(z, 0.05)
        return (self.cx + self.f * x / z, self.cy + self.f * y / z)

    def scale(self, z):
        """Pixel pro Meter in Tiefe z."""
        return self.f / max(z, 0.05)

    def floor_y(self):
        """Y-Koordinate des Bodens (Kamera auf Augenhöhe)."""
        return self.eye

    def quad(self, ctx, pts3, color, lw=P.LW, alpha=1.0):
        P.poly(ctx, [self.p(*q) for q in pts3], color, lw, alpha=alpha)

    def box(self, ctx, x0, x1, y0, y1, z0, z1, front, top=None, side=None, lw=P.LW):
        """Quader: zeigt die Front (z0), Oberseite und die zur Mitte zeigende Seite."""
        top = top or P.shade(front, 1.15)
        side = side or P.shade(front, 0.8)
        # Seite (sichtbar, wenn der Quader seitlich von der Kamera liegt)
        if x0 > 0:
            self.quad(ctx, [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], side, lw)
        elif x1 < 0:
            self.quad(ctx, [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], side, lw)
        # Oberseite (sichtbar, wenn unter Augenhöhe)
        if y0 > 0:
            self.quad(ctx, [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], top, lw)
        elif y1 < 0:
            self.quad(ctx, [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], top, lw)
        self.quad(ctx, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], front, lw)
