"""A small flow-field line packer.

Lines follow an angle field and stop before they touch each other, the edge
of the canvas or anything in an exclusion mask (used to carve text out of the
field). The result is a list of smooth polylines with a width and a colour.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFilter
from fontTools.pens.basePen import BasePen

TAU = math.tau


class Noise:
    """2D gradient noise (Perlin), deterministic for a seed."""

    def __init__(self, seed: int):
        rnd = random.Random(seed)
        p = list(range(256))
        rnd.shuffle(p)
        self.p = p + p
        self.g = [(math.cos(a), math.sin(a)) for a in (rnd.random() * TAU for _ in range(256))]

    def __call__(self, x: float, y: float) -> float:
        xi, yi = math.floor(x), math.floor(y)
        xf, yf = x - xi, y - yi
        xi &= 255
        yi &= 255
        p, g = self.p, self.g

        def dot(ix, iy, dx, dy):
            gx, gy = g[p[p[ix] + iy] & 255]
            return gx * dx + gy * dy

        u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
        v = yf * yf * yf * (yf * (yf * 6 - 15) + 10)
        a = dot(xi, yi, xf, yf)
        b = dot(xi + 1, yi, xf - 1, yf)
        c = dot(xi, yi + 1, xf, yf - 1)
        d = dot(xi + 1, yi + 1, xf - 1, yf - 1)
        return (a + u * (b - a)) + v * ((c + u * (d - c)) - (a + u * (b - a)))


@dataclass
class Line:
    pts: list[tuple[float, float]]
    width: float
    color: str
    dotted: bool = False
    meta: dict = field(default_factory=dict)

    @property
    def length(self) -> float:
        return sum(math.dist(a, b) for a, b in zip(self.pts, self.pts[1:]))


class Occupancy:
    def __init__(self, w: int, h: int, cell: float = 12.0):
        self.cell = cell
        self.cols = int(w / cell) + 2
        self.grid: dict[tuple[int, int], list[tuple[float, float, float]]] = {}

    def free(self, x: float, y: float, r: float, gap: float, ignore: int = -1) -> bool:
        cx, cy = int(x / self.cell), int(y / self.cell)
        reach = int((r + gap + 14) / self.cell) + 1
        for i in range(cx - reach, cx + reach + 1):
            for j in range(cy - reach, cy + reach + 1):
                for px, py, pr, owner in self.grid.get((i, j), ()):
                    if owner == ignore:
                        continue
                    if (px - x) ** 2 + (py - y) ** 2 < (pr + r + gap) ** 2:
                        return False
        return True

    def add(self, pts, r: float, owner: int):
        for x, y in pts:
            self.grid.setdefault((int(x / self.cell), int(y / self.cell)), []).append((x, y, r, owner))


class _FlattenPen(BasePen):
    def __init__(self, glyphset, transform):
        super().__init__(glyphset)
        self.t = transform
        self.contours: list[list[tuple[float, float]]] = []
        self.cur: list[tuple[float, float]] = []

    def _xy(self, p):
        s, ox, oy = self.t
        return (ox + p[0] * s, oy - p[1] * s)

    def _moveTo(self, p):
        self.cur = [self._xy(p)]

    def _lineTo(self, p):
        self.cur.append(self._xy(p))

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        for i in range(1, 9):
            t = i / 8
            mt = 1 - t
            x = mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0]
            y = mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]
            self.cur.append(self._xy((x, y)))

    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        for i in range(1, 7):
            t = i / 6
            mt = 1 - t
            x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
            y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
            self.cur.append(self._xy((x, y)))

    def _closePath(self):
        if len(self.cur) > 2:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


class Mask:
    """Pixels where lines may not go."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.img = Image.new("L", (w, h), 0)
        self.draw = ImageDraw.Draw(self.img)
        self.px = None

    def text(self, face, content: str, x: float, y: float, size: float, tracking: float = 0):
        runs, _ = face.glyph_runs(content, x, y, size, tracking)
        s = size / face.upem
        for name, gx, gy in runs:
            pen = _FlattenPen(face.glyphs, (s, gx, gy))
            face.glyphs[name].draw(pen)
            for contour in pen.contours:
                self.draw.polygon(contour, fill=255)

    def rect(self, x0, y0, x1, y1):
        self.draw.rectangle((x0, y0, x1, y1), fill=255)

    def grow(self, px: int):
        size = px * 2 + 1
        self.img = self.img.filter(ImageFilter.MaxFilter(size))
        self.draw = ImageDraw.Draw(self.img)

    def blocked(self, x: float, y: float) -> bool:
        if self.px is None:
            self.px = self.img.load()
        xi, yi = int(x), int(y)
        if not (0 <= xi < self.w and 0 <= yi < self.h):
            return True
        return self.px[xi, yi] > 0


def pack(w: int, h: int, angle, *, seed: int, colors: list[tuple[str, float]],
         widths: list[tuple[float, float]], margin: float = 10, gap: float = 3.0,
         spacing: float = 11.0, step: float = 2.5, min_len: float = 36, max_len: float = 520,
         mask: Mask | None = None, dotted_share: float = 0.0, density=None) -> list[Line]:
    """Grow non-overlapping lines along `angle(x, y)` (radians)."""
    rnd = random.Random(seed)
    occ = Occupancy(w, h)
    seeds = [(x + rnd.uniform(-spacing / 2, spacing / 2), y + rnd.uniform(-spacing / 2, spacing / 2))
             for x in frange(margin, w - margin, spacing) for y in frange(margin, h - margin, spacing)]
    rnd.shuffle(seeds)

    def pick(options):
        r = rnd.random() * sum(p for _, p in options)
        for v, p in options:
            r -= p
            if r <= 0:
                return v
        return options[-1][0]

    def ok(x, y, r):
        if x < margin + r or y < margin + r or x > w - margin - r or y > h - margin - r:
            return False
        if mask and mask.blocked(x, y):
            return False
        return True

    lines: list[Line] = []
    for sx, sy in seeds:
        if density and rnd.random() > density(sx, sy):
            continue
        width = pick(widths)
        r = width / 2
        if not ok(sx, sy, r) or not occ.free(sx, sy, r, gap):
            continue
        halves = []
        for direction in (1, -1):
            pts = [(sx, sy)]
            x, y = sx, sy
            travelled = 0.0
            while travelled < max_len / 2:
                a = angle(x, y)
                nx, ny = x + math.cos(a) * step * direction, y + math.sin(a) * step * direction
                if not ok(nx, ny, r) or not occ.free(nx, ny, r, gap):
                    break
                pts.append((nx, ny))
                x, y = nx, ny
                travelled += step
            halves.append(pts)
        pts = list(reversed(halves[1]))[:-1] + halves[0]
        line = Line(pts, width, pick(colors), dotted=width <= 7 and rnd.random() < dotted_share * 2)
        if line.length < min_len:
            continue
        occ.add(pts[::2], r, len(lines))
        lines.append(line)
    return lines


def frange(a: float, b: float, s: float):
    v = a
    while v < b:
        yield v
        v += s


def smooth_path(pts: list[tuple[float, float]], every: float = 10.0) -> str:
    """Resample a polyline and draw it as a Catmull-Rom spline."""
    sampled = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        acc += math.dist(a, b)
        if acc >= every:
            sampled.append(b)
            acc = 0.0
    if sampled[-1] != pts[-1]:
        sampled.append(pts[-1])
    if len(sampled) < 3:
        (x0, y0), (x1, y1) = sampled[0], sampled[-1]
        return f"M{x0:.0f} {y0:.0f}L{x1:.0f} {y1:.0f}"
    out = [f"M{sampled[0][0]:.0f} {sampled[0][1]:.0f}"]
    for i in range(len(sampled) - 1):
        p0 = sampled[i - 1] if i else sampled[i]
        p1, p2 = sampled[i], sampled[i + 1]
        p3 = sampled[i + 2] if i + 2 < len(sampled) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(f"C{c1[0]:.0f} {c1[1]:.0f} {c2[0]:.0f} {c2[1]:.0f} {p2[0]:.0f} {p2[1]:.0f}")
    return "".join(out).replace(" -", "-")
