"""Shared helpers for the profile artwork.

Every SVG in assets/ is generated from these helpers. Text is converted to
vector paths with HarfBuzz shaping, so the images look identical everywhere:
GitHub renders README images in a sandbox that cannot load web fonts.
"""

from __future__ import annotations

import io
import json
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = Path(__file__).resolve().parent / "fonts"
ICONS = json.loads((Path(__file__).resolve().parent / "icons.json").read_text())


# Night and day versions of an indoor map. The navy ground and wayfinding
# yellow come from mall and airport signage; the blue is the position dot.
PALETTES = {
    "dark": {
        "bg": "#0D1B2E",
        "room": "#13253D",
        "room2": "#182D4A",
        "wall": "#2E4A70",
        "line": "#22385A",
        "ink": "#E9EEF6",
        "muted": "#93A3BB",
        "blue": "#4DA3FF",
        "halo": "#4DA3FF",
        "sign": "#FFC530",
        "sign_ink": "#0D1B2E",
        "step": "#C9D6E8",
        "dest_fill": (0, 0.07),
        "mark": "#FFC530",
        "heat": ["#182D4A", "#1D4677", "#2A69B4", "#4DA3FF", "#B5DAFF"],
    },
    "light": {
        "bg": "#EEF2F7",
        "room": "#FFFFFF",
        "room2": "#E3E9F1",
        "wall": "#A3B3C8",
        "line": "#CBD5E2",
        "ink": "#0D1B2E",
        "muted": "#53647C",
        "blue": "#1A6FE0",
        "halo": "#1A6FE0",
        "sign": "#FFC530",
        "sign_ink": "#0D1B2E",
        "step": "#3B4E69",
        "dest_fill": (0.12, 0.28),
        "mark": "#D99A00",
        "heat": ["#E3E9F1", "#B7D1F4", "#6EA5EC", "#1A6FE0", "#0B3F8C"],
    },
}


def num(v: float) -> str:
    """Compact number formatting for SVG attributes."""
    s = f"{v:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    if s == "-0":
        s = "0"
    return s


class Face:
    def __init__(self, weight: int):
        tt = TTFont(FONTS / f"overpass-{weight}.woff")
        tt.flavor = None
        buf = io.BytesIO()
        tt.save(buf)
        self.tt = TTFont(io.BytesIO(buf.getvalue()))
        self.upem = self.tt["head"].unitsPerEm
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.hb = hb.Font(hb.Face(hb.Blob(buf.getvalue())))
        self.ascender = self.tt["hhea"].ascent
        self.cap = getattr(self.tt["OS/2"], "sCapHeight", 0) or int(self.upem * 0.7)

    def _shape(self, text: str, features: dict | None = None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, features or {"kern": True, "liga": True})
        return buf.glyph_infos, buf.glyph_positions

    def measure(self, text: str, size: float, tracking: float = 0, features=None) -> float:
        infos, pos = self._shape(text, features)
        units = sum(p.x_advance for p in pos) + tracking * self.upem * max(len(infos) - 1, 0)
        return units * size / self.upem

    def glyph_runs(self, text: str, x: float, y: float, size: float, tracking: float = 0,
                   anchor: str = "start", features=None):
        """Yield (glyph name, x, y) placements for `text` with its baseline at y."""
        width = self.measure(text, size, tracking, features)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        infos, pos = self._shape(text, features)
        s = size / self.upem
        pen_x = 0.0
        out = []
        for info, p in zip(infos, pos):
            name = self.order[info.codepoint]
            out.append((name, x + (pen_x + p.x_offset) * s, y - p.y_offset * s))
            pen_x += p.x_advance + tracking * self.upem
        return out, width

    def outline(self, name: str) -> str:
        pen = SVGPathPen(self.glyphs, ntos=lambda v: str(round(v)))
        self.glyphs[name].draw(pen)
        return pen.getCommands()

    def wrap(self, text: str, size: float, max_width: float, tracking: float = 0) -> list[str]:
        words = text.split()
        lines: list[str] = []
        cur = ""
        for w in words:
            trial = f"{cur} {w}".strip()
            if self.measure(trial, size, tracking) <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines


@lru_cache(maxsize=None)
def face(weight: int) -> Face:
    return Face(weight)


# Glyphs used by the document being built. Each one is stored once in <defs>
# and placed with <use>, which keeps text-heavy images small.
_GLYPHS: dict[str, str] = {}


def text(content: str, x: float, y: float, size: float, weight: int = 500, fill: str = "#000",
         anchor: str = "start", tracking: float = 0, extra: str = "", features=None) -> str:
    f = face(weight)
    runs, _ = f.glyph_runs(content, x, y, size, tracking, anchor, features)
    s = size / f.upem
    uses = []
    for name, gx, gy in runs:
        gid = f"g{weight}{name}".replace(".", "_")
        if gid not in _GLYPHS:
            d = f.outline(name)
            _GLYPHS[gid] = d
        if _GLYPHS[gid]:
            uses.append(f'<use href="#{gid}" transform="matrix({s:.5f} 0 0 {-s:.5f} {num(gx)} {num(gy)})"/>')
    return f'<g fill="{fill}"{extra}>{"".join(uses)}</g>'


def measure(content: str, size: float, weight: int = 500, tracking: float = 0) -> float:
    return face(weight).measure(content, size, tracking)


def wrap(content: str, size: float, max_width: float, weight: int = 500) -> list[str]:
    return face(weight).wrap(content, size, max_width)


def icon(name: str, x: float, y: float, size: float, fill: str) -> str:
    """A Simple Icons glyph (24x24 grid) placed at x, y."""
    s = size / 24
    return (f'<path fill="{fill}" transform="translate({num(x)} {num(y)}) scale({s:.4f})" '
            f'd="{ICONS[name]["path"]}"/>')


def svg(width: int, height: int, body: str, title: str, style: str = "") -> str:
    style_block = f"<style>{style}</style>" if style else ""
    defs = "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in _GLYPHS.items() if d)
    _GLYPHS.clear()
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">'
        f"<title>{title}</title>{style_block}<defs>{defs}</defs>{body}</svg>\n"
    )


def write(name: str, content: str) -> None:
    ElementTree.fromstring(content)  # refuse to write malformed XML
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(content, encoding="utf-8")
    print(f"  {name:32s} {len(content.encode()) / 1024:6.1f} KB")
