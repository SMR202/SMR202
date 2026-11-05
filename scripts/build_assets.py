"""Builds the static profile artwork in assets/ (dark and light versions).

    pip install -r scripts/requirements.txt
    python scripts/build_assets.py

The activity panel is rendered separately by scripts/activity.py, which a
GitHub Action runs every day.
"""

from __future__ import annotations

import math
import random

from kit import PALETTES, icon, measure, num, svg, text, wrap, write

REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


# ---------------------------------------------------------------- hero ----

W, H = 1200, 600
T = 14.0  # seconds per loop

# Floor plan: one level of a mall. Corridors are the bare ground colour.
OUTER = (40, 40, 1160, 560)
NORTH = [  # (x0, y0, x1, y1, door x or None, label)
    (40, 40, 190, 268, 140, "G01"),
    (190, 40, 340, 268, 290, "G02"),
    (340, 40, 470, 268, 420, "G03"),
    (470, 40, 610, 268, 560, "G04"),
    (610, 40, 748, 268, 690, "G05"),
    (870, 40, 960, 268, 905, "G07"),
]
DEST = (960, 40, 1160, 268, 1015, "G08")
CORE = (748, 40, 870, 268)
SOUTH = [
    (40, 332, 200, 560, 70, "G15"),
    (200, 332, 350, 560, 230, "G14"),
    (350, 332, 500, 560, 380, "G13"),
    (500, 332, 630, 560, 530, "G12"),
]
S5 = (630, 332, 748, 560, "G11")  # door on its east wall
S6 = (812, 332, 960, 450, "G09")  # door on its west wall
S7 = (812, 450, 960, 560, "G10")
FOOD = (960, 332, 1160, 560)

ROUTE = [(780, 528), (780, 300), (1030, 300), (1030, 166)]
WALK_START, WALK_END = 3.4, 11.4


def pct(t: float) -> str:
    return f"{t / T * 100:.2f}%"


def seg_lengths(pts):
    return [math.dist(a, b) for a, b in zip(pts, pts[1:])]


def point_at(pts, s):
    for (a, b), L in zip(zip(pts, pts[1:]), seg_lengths(pts)):
        if s <= L:
            f = s / L
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f,
                    math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
        s -= L
    a, b = pts[-2], pts[-1]
    return b[0], b[1], math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def walkable(x, y):
    in_h = 40 < x < 1160 and 270 < y < 330
    in_v = 750 < x < 810 and 330 <= y < 558
    return in_h or in_v


def floor_plan(c):
    o = []
    rooms = [r[:4] for r in NORTH] + [r[:4] for r in SOUTH] + [S5[:4], S6[:4], S7[:4], FOOD, CORE]
    for x0, y0, x1, y1 in rooms:
        fill = c["room2"] if (x0, y0, x1, y1) == CORE else c["room"]
        o.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{fill}" '
                 f'stroke="{c["wall"]}" stroke-width="2"/>')

    # destination unit, tinted in signage yellow
    x0, y0, x1, y1 = DEST[:4]
    o.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{c["room"]}" '
             f'stroke="{c["wall"]}" stroke-width="2"/>')
    o.append(f'<rect class="dest" x="{x0 + 5}" y="{y0 + 5}" width="{x1 - x0 - 10}" height="{y1 - y0 - 10}" '
             f'rx="3" fill="{c["sign"]}" fill-opacity="{c["dest_fill"][0]}" stroke="{c["sign"]}" stroke-width="2"/>')

    # doors: a gap in the wall, the leaf and its swing
    gap = c["room"]
    def door_h(x, wall_y, into):  # into = -1 room above, +1 room below
        leaf_y = wall_y + 30 * into
        sweep = 1 if into < 0 else 0
        o.append(f'<rect x="{x}" y="{wall_y - 1.6}" width="30" height="3.2" fill="{gap}"/>')
        o.append(f'<path d="M{x} {wall_y}V{leaf_y}A30 30 0 0 {sweep} {x + 30} {wall_y}" fill="none" '
                 f'stroke="{c["wall"]}" stroke-width="1.5"/>')

    def door_v(wall_x, y, into):  # into = +1 room to the right, -1 room to the left
        leaf_x = wall_x + 30 * into
        sweep = 1 if into > 0 else 0
        o.append(f'<rect x="{wall_x - 1.6}" y="{y}" width="3.2" height="30" fill="{gap}"/>')
        o.append(f'<path d="M{wall_x} {y}H{leaf_x}A30 30 0 0 {sweep} {wall_x} {y + 30}" fill="none" '
                 f'stroke="{c["wall"]}" stroke-width="1.5"/>')

    for r in NORTH + [DEST]:
        door_h(r[4], 268, -1)
    for r in SOUTH:
        door_h(r[4], 332, +1)
    door_v(748, 440, -1)
    door_v(812, 376, +1)
    door_v(812, 492, +1)

    # food court: open frontage and tables
    o.append(f'<rect x="992" y="330.4" width="136" height="3.2" fill="{c["room"]}"/>')
    for tx in (1012, 1062, 1112):
        for ty in (380, 428, 476):
            o.append(f'<circle cx="{tx}" cy="{ty}" r="10" fill="none" stroke="{c["wall"]}" stroke-width="1.5"/>')

    # service core: two lifts and a stair
    o.append(f'<rect x="788" y="266.4" width="44" height="3.2" fill="{c["room2"]}"/>')
    for lx in (762, 810):
        o.append(f'<rect x="{lx}" y="56" width="40" height="40" fill="none" stroke="{c["wall"]}" stroke-width="1.5"/>'
                 f'<path d="M{lx} 56l40 40M{lx + 40} 56l-40 40" stroke="{c["wall"]}" stroke-width="1.2"/>')
    o.append(f'<rect x="762" y="116" width="88" height="128" fill="none" stroke="{c["wall"]}" stroke-width="1.5"/>')
    hatch = "".join(f"M762 {y}h88" for y in range(126, 244, 11))
    o.append(f'<path d="{hatch}" stroke="{c["wall"]}" stroke-width="1"/>')
    o.append(f'<path d="M806 236V128m-7 9 7-9 7 9" fill="none" stroke="{c["wall"]}" stroke-width="1.5" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')

    # outer wall with the entrance
    x0, y0, x1, y1 = OUTER
    o.append(f'<path d="M756 {y1}H{x0}V{y0}H{x1}V{y1}H804" fill="none" stroke="{c["wall"]}" '
             f'stroke-width="4" stroke-linejoin="round"/>')
    o.append(f'<path d="M756 {y1 - 4}h20M784 {y1 + 4}h20" stroke="{c["wall"]}" stroke-width="2"/>')

    # unit numbers
    labels = [(r[0], r[1], r[5]) for r in NORTH + [DEST] + SOUTH] + [(S5[0], S5[1], S5[4]),
                                                                    (S6[0], S6[1], S6[4]),
                                                                    (S7[0], S7[1], S7[4])]
    for lx, ly, lab in labels:
        o.append(text(lab, lx + 14, ly + 28, 14, 700, c["muted"], extra=' opacity="0.6"'))
    o.append(text("Food court", 1146, 546, 14, 700, c["muted"], "end", extra=' opacity="0.6"'))
    return "".join(o)


def pin(x, y, c, scale=1.0):
    return (f'<g transform="translate({num(x)} {num(y)}) scale({scale})">'
            f'<path d="M0 0C-4-9-15-17-15-30A15 15 0 1 1 15-30C15-17 4-9 0 0Z" fill="{c["sign"]}" '
            f'stroke="{c["sign_ink"]}" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<circle cy="-30" r="5.5" fill="{c["sign_ink"]}"/></g>')


def hero(mode: str) -> str:
    c = PALETTES[mode]
    rnd = random.Random(202)
    css = []
    body = []

    body.append(f'<defs><linearGradient id="fadeg" x1="0" x2="1" y1="0" y2="0">'
                f'<stop offset="0" stop-color="#fff" stop-opacity="0.13"/>'
                f'<stop offset="0.36" stop-color="#fff" stop-opacity="0.13"/>'
                f'<stop offset="0.6" stop-color="#fff" stop-opacity="1"/></linearGradient>'
                f'<mask id="fade"><rect width="{W}" height="{H}" fill="url(#fadeg)"/></mask>'
                f'<clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath></defs>')
    body.append(f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{c["bg"]}"/>')
    body.append(f'<g mask="url(#fade)">{floor_plan(c)}</g>')

    # planned route
    L = sum(seg_lengths(ROUTE))
    d = "M" + "L".join(f"{x} {y}" for x, y in ROUTE)
    body.append(f'<path class="rt" d="{d}" fill="none" stroke="{c["bg"]}" stroke-width="15" '
                f'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{L:.0f}" stroke-dashoffset="0"/>')
    body.append(f'<path class="rt" d="{d}" fill="none" stroke="{c["blue"]}" stroke-opacity="0.9" stroke-width="7" '
                f'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{L:.0f}" stroke-dashoffset="0"/>')
    css.append(f".rt{{animation:rt {T}s infinite}}"
               f"@keyframes rt{{0%,{pct(0.4)}{{stroke-dashoffset:{L:.0f};opacity:1}}"
               f"{pct(2.4)}{{stroke-dashoffset:0}}{pct(12.5)}{{opacity:1}}"
               f"{pct(13.2)},100%{{opacity:0;stroke-dashoffset:0}}}}")

    # detected steps, dropped behind the walker
    speed = L / (WALK_END - WALK_START)
    s, k, steps = 12.0, 0, []
    while s < L - 8:
        x, y, ang = point_at(ROUTE, s)
        side = 11 if k % 2 else -11
        nx, ny = -math.sin(math.radians(ang)) * side, math.cos(math.radians(ang)) * side
        t = WALK_START + s / speed
        steps.append(f'<ellipse class="s{k}" cx="0" cy="0" rx="4.8" ry="2.6" fill="{c["step"]}" opacity="0.7" '
                     f'transform="translate({num(x + nx)} {num(y + ny)}) rotate({ang:.0f})"/>')
        css.append(f".s{k}{{animation:s{k} {T}s linear infinite}}"
                   f"@keyframes s{k}{{0%,{pct(t)}{{opacity:0}}{pct(t + 0.08)}{{opacity:.75}}"
                   f"{pct(12.5)}{{opacity:.75}}{pct(13.2)},100%{{opacity:0}}}}")
        s += 21.0
        k += 1
    body.append("".join(steps))

    # destination
    ex, ey = ROUTE[-1]
    base, peak = c["dest_fill"]
    css.append(f".dest{{animation:dest {T}s infinite}}"
               f"@keyframes dest{{0%,{pct(WALK_END)}{{fill-opacity:{base}}}{pct(WALK_END + 0.5)}{{fill-opacity:{peak}}}"
               f"{pct(12.8)}{{fill-opacity:{peak}}}{pct(13.6)},100%{{fill-opacity:{base}}}}}")
    rings = ""
    for i, delay in enumerate((0.0, 0.45)):
        a, b = WALK_END + delay, WALK_END + delay + 1.3
        rings += (f'<circle class="r{i}" r="13" fill="none" stroke="{c["sign"]}" stroke-width="3" opacity="0"/>')
        css.append(f".r{i}{{animation:r{i} {T}s ease-out infinite}}"
                   f"@keyframes r{i}{{0%,{pct(a)}{{transform:scale(1);opacity:0}}{pct(a + 0.05)}{{opacity:.95}}"
                   f"{pct(b)},100%{{transform:scale(3.4);opacity:0}}}}")
    body.append(f'<g transform="translate({ex} {ey})">{rings}</g>')
    body.append(pin(ex, ey - 8, c))

    # the walker: particles, uncertainty halo, heading cone and the dot
    sx, sy = ROUTE[0]
    valid, pruned = [], []
    while len(valid) < 46 or len(pruned) < 40:
        dx, dy = rnd.gauss(0, 78), rnd.gauss(-10, 74)
        bucket = valid if walkable(sx + dx, sy + dy) else pruned
        if len(bucket) < (46 if bucket is valid else 40):
            bucket.append((dx, dy))

    parts = []
    for i, (dx, dy) in enumerate(valid + pruned):
        is_valid = i < len(valid)
        jx, jy = rnd.gauss(0, 4), rnd.gauss(0, 4)
        frames = [f"0%{{transform:translate({dx:.0f}px,{dy:.0f}px);opacity:0}}",
                  f"{pct(0.5)}{{transform:translate({dx:.0f}px,{dy:.0f}px);opacity:.85}}"]
        if is_valid:
            for t, spread in ((3.2, 6), (4.8, 8), (6.3, 10), (7.9, 8), (9.6, 10), (11.0, 7), (12.0, 4)):
                frames.append(f"{pct(t)}{{transform:translate({rnd.gauss(0, spread):.1f}px,"
                              f"{rnd.gauss(0, spread):.1f}px);opacity:.85}}")
            frames.append(f"{pct(12.5)}{{opacity:.85}}{pct(13.2)},100%{{opacity:0}}")
            base_opacity = "0.85"
        else:
            t_out = rnd.uniform(0.9, 2.2)
            frames.append(f"{pct(t_out)}{{opacity:.85}}{pct(t_out + 0.35)},100%"
                          f"{{transform:translate({dx:.0f}px,{dy:.0f}px);opacity:0}}")
            base_opacity = "0"
        parts.append(f'<circle class="p{i}" r="2.4" fill="{c["blue"]}" opacity="{base_opacity}" '
                     f'style="transform:translate({jx:.1f}px,{jy:.1f}px)"/>')
        css.append(f".p{i}{{animation:p{i} {T}s ease-in-out infinite}}@keyframes p{i}{{{''.join(frames)}}}")

    walk_frames = [f"0%,{pct(WALK_START)}{{transform:translate({sx}px,{sy}px)}}"]
    t = WALK_START
    for (a, b), seg in zip(zip(ROUTE, ROUTE[1:]), seg_lengths(ROUTE)):
        t += seg / speed
        walk_frames.append(f"{pct(t)}{{transform:translate({b[0]}px,{b[1]}px)}}")
    walk_frames.append(f"100%{{transform:translate({ex}px,{ey}px)}}")
    css.append(f".wk{{animation:wk {T}s linear infinite}}@keyframes wk{{{''.join(walk_frames)}}}")

    # heading: north, then east at the first corner, north again at the second
    t1 = WALK_START + seg_lengths(ROUTE)[0] / speed
    t2 = t1 + seg_lengths(ROUTE)[1] / speed
    css.append(f".hd{{animation:hd {T}s ease-in-out infinite}}"
               f"@keyframes hd{{0%,{pct(t1 - 0.2)}{{transform:rotate(-90deg)}}{pct(t1 + 0.2)},"
               f"{pct(t2 - 0.2)}{{transform:rotate(0deg)}}{pct(t2 + 0.2)},100%{{transform:rotate(-90deg)}}}}")
    css.append(f".hl{{animation:hl {T}s ease-in-out infinite}}"
               f"@keyframes hl{{0%,{pct(0.5)}{{transform:scale(3.9)}}{pct(3.2)},100%{{transform:scale(1)}}}}")
    css.append(f".dt{{animation:dt {T}s infinite}}"
               f"@keyframes dt{{0%{{opacity:0}}{pct(0.5)},{pct(12.6)}{{opacity:1}}{pct(13.3)},100%{{opacity:0}}}}")

    body.append(
        f'<g class="wk" style="transform:translate({ex}px,{ey}px)">'
        f'<g>{"".join(parts)}</g>'
        f'<g class="dt">'
        f'<circle class="hl" r="19" fill="{c["halo"]}" fill-opacity="0.16" stroke="{c["halo"]}" '
        f'stroke-opacity="0.55" stroke-width="1.5"/>'
        f'<path class="hd" style="transform:rotate(-90deg)" d="M0 0L34-15A37 37 0 0 1 34 15Z" '
        f'fill="{c["blue"]}" fill-opacity="0.35"/>'
        f'<circle r="9.5" fill="{c["blue"]}" stroke="#FFFFFF" stroke-width="3.5"/></g></g>'
    )

    # title block
    body.append(text("Sameer", 70, 168, 122, 900, c["ink"], tracking=-0.012))
    body.append(text("Amjad", 70, 280, 122, 900, c["ink"], tracking=-0.012))
    body.append(text("Indoor positioning, real-time systems", 74, 338, 27, 500, c["muted"]))
    body.append(text("and the web, built in Islamabad.", 74, 374, 27, 500, c["muted"]))

    # legend, so the animation explains itself
    lx, ly = 74, 456
    body.append(text("How TURN finds you", lx, ly, 20, 700, c["ink"]))
    r1, r2, cx2 = ly + 40, ly + 76, lx + 226
    body.append(f'<circle cx="{lx + 11}" cy="{r1 - 6}" r="13" fill="{c["halo"]}" fill-opacity="0.16" '
                f'stroke="{c["halo"]}" stroke-opacity="0.55" stroke-width="1.2"/>'
                f'<circle cx="{lx + 11}" cy="{r1 - 6}" r="6" fill="{c["blue"]}" stroke="#FFFFFF" stroke-width="2.2"/>')
    body.append(text("Position estimate", lx + 34, r1, 18, 600, c["muted"]))
    for dx, dy in ((0, -2), (8, -9), (13, 1), (4, 6), (17, -6)):
        body.append(f'<circle cx="{cx2 + 2 + dx}" cy="{r1 - 6 + dy}" r="2.4" fill="{c["blue"]}" opacity="0.85"/>')
    body.append(text("Particles", cx2 + 34, r1, 18, 600, c["muted"]))
    body.append(f'<ellipse cx="{lx + 6}" cy="{r2 - 3}" rx="2.6" ry="4.8" fill="{c["step"]}" opacity="0.75"/>'
                f'<ellipse cx="{lx + 16}" cy="{r2 - 11}" rx="2.6" ry="4.8" fill="{c["step"]}" opacity="0.75"/>')
    body.append(text("Detected steps", lx + 34, r2, 18, 600, c["muted"]))
    body.append(pin(cx2 + 11, r2 + 3, c, 0.6))
    body.append(text("Destination", cx2 + 34, r2, 18, 600, c["muted"]))
    body.append(text("Entrance", 780, 590, 14, 700, c["muted"], "middle", extra=' opacity="0.8"'))

    body.append("</g>")
    return svg(W, H, "".join(body),
               "Sameer Amjad. Indoor positioning, real-time systems and the web, built in Islamabad.",
               "".join(css) + REDUCED)


# ------------------------------------------------------- pictograms ----
# Drawn on a 100 x 100 grid in the style of wayfinding symbols.

def picto(name: str, ink: str) -> str:
    def st(w: float = 8) -> str:
        return (f'fill="none" stroke="{ink}" stroke-width="{w}" '
                f'stroke-linecap="round" stroke-linejoin="round"')
    if name == "turn":
        return (f'<path d="M58 8C44 8 34 18 34 31C34 47 58 70 58 70S82 47 82 31C82 18 72 8 58 8Z" fill="{ink}"/>'
                f'<circle cx="58" cy="31" r="8" fill="#FFC530"/>'
                f'<ellipse cx="20" cy="76" rx="7.5" ry="11" transform="rotate(-18 20 76)" fill="{ink}"/>'
                f'<ellipse cx="40" cy="90" rx="7.5" ry="11" transform="rotate(-18 40 90)" fill="{ink}"/>')
    if name == "lumen":
        bars = "".join(f'<path d="M{x} {88 - h / 2}V{88 + h / 2}" {st(6)}/>'
                       for x, h in ((14, 8), (26, 18), (38, 12), (50, 22), (62, 10), (74, 16), (86, 6)))
        return (f'<rect x="8" y="8" width="84" height="58" rx="10" {st()}/>'
                f'<path d="M42 23L62 37L42 51Z" fill="{ink}" stroke="{ink}" stroke-width="4" stroke-linejoin="round"/>'
                + bars)
    if name == "twin":
        return (f'<rect x="6" y="50" width="32" height="32" rx="6" fill="{ink}"/>'
                f'<rect x="62" y="50" width="32" height="32" rx="6" {st(7)}/>'
                f'<path d="M38 66H62" {st(6)} stroke-dasharray="1 11"/>'
                f'<path d="M30 30A28 28 0 0 1 70 30" {st(7)}/>'
                f'<path d="M40 40A14 14 0 0 1 60 40" {st(7)}/>')
    if name == "plane":
        return (f'<g transform="rotate(45 50 50)"><path d="M50 4C55 4 57 10 57 18V40L92 60V70L57 59V80L68 88V95'
                f'L50 90L32 95V88L43 80V59L8 70V60L43 40V18C43 10 45 4 50 4Z" fill="{ink}"/></g>')
    if name == "neuro":
        nodes = [(20, 24), (50, 12), (80, 28), (30, 62), (66, 58), (50, 90), (88, 78)]
        edges = [(0, 1), (1, 2), (0, 3), (1, 4), (2, 4), (3, 4), (3, 5), (4, 5), (4, 6)]
        lines = "".join(f'<path d="M{nodes[a][0]} {nodes[a][1]}L{nodes[b][0]} {nodes[b][1]}" {st(5)}/>'
                        for a, b in edges)
        dots = "".join(f'<circle cx="{x}" cy="{y}" r="{11 if i == 4 else 8}" fill="{ink}"/>'
                       for i, (x, y) in enumerate(nodes))
        return lines + dots
    if name == "merkle":
        return (f'<path d="M50 22V34M50 34H26V52M50 34H74V52M26 52H14V70M26 52H38V70M74 52H62V70M74 52H86V70" '
                f'{st(5)}/>'
                f'<rect x="36" y="6" width="28" height="20" rx="4" fill="{ink}"/>'
                + "".join(f'<rect x="{x - 9}" y="70" width="18" height="22" rx="3" fill="{ink}"/>'
                          for x in (14, 38, 62, 86)))
    if name == "shop":
        return (f'<path d="M10 40V90H90V40" {st(7)}/>'
                f'<path d="M6 10H94L98 34C98 42 90 46 84 46C77 46 72 41 72 34C72 41 66 46 59 46'
                f'C52 46 46 41 46 34C46 41 40 46 33 46C26 46 20 41 20 34C20 41 14 46 8 46C4 46 2 40 2 34Z" fill="{ink}"/>'
                f'<rect x="58" y="58" width="20" height="32" fill="{ink}"/>'
                f'<rect x="22" y="58" width="26" height="18" rx="2" {st(6)}/>')
    raise KeyError(name)


# ------------------------------------------------------ work panels ----

WORK = [
    dict(key="turn", picto="turn", title="TURN",
         note="Final-year project",
         desc="Indoor navigation for malls without installing beacons. I own positioning: "
              "step detection, heading, and a particle filter that rules out paths through walls.",
         stack="Android, sensor fusion, particle filters, Python"),
    dict(key="lumen", picto="lumen", title="Lumen",
         note="Team project",
         desc="Watches live streams or recorded videos, then transcribes, reads the frames, "
              "summarizes and answers questions about them through a ten-stage pipeline.",
         stack="Python, FastAPI, Whisper, Gemini, FFmpeg, Next.js"),
    dict(key="twin", picto="twin", title="Digital twins on bad networks",
         note="Research",
         desc="How MQTT QoS levels and edge buffering change freshness, delivery and recovery "
              "time when a cloud digital twin loses its connection.",
         stack="MQTT, edge computing, cloud, experiment design"),
    dict(key="aircontrolx", picto="plane", title="AirControlX",
         note="Operating systems",
         desc="Air traffic control simulation for three runways: arrivals, departures, emergencies "
              "and violation notices, run on POSIX threads with Unix pipes and drawn in SFML.",
         stack="C++, POSIX threads, IPC, SFML"),
    dict(key="neurozehn", picto="neuro", title="NeuroZehn",
         note="Client website",
         desc="A 61-page site for a brain-health institute, with Urdu right-to-left interface previews, "
              "accessible figures and every claim traced back to the client's source documents.",
         stack="Next.js, TypeScript, Tailwind CSS, Zod"),
    dict(key="merkle", picto="merkle", title="Integrity verification",
         note="Data structures",
         desc="SHA-256 Merkle trees over a million product reviews. Detects edits, deletions and "
              "insertions, and checks existence proofs in under 100 ms.",
         stack="Python, SHA-256, CustomTkinter"),
    dict(key="clients", picto="shop", title="Sites for Islamabad businesses",
         note="Freelance",
         desc="Twenty-plus sites and pitch builds for cafés, salons, bakeries, a furniture maker, "
              "a school and a collector-car marketplace. Some run their catalogue from a spreadsheet.",
         stack="Next.js, React, Sanity, Google Sheets, Vercel"),
]

PW, PH = 1200, 214


def panel(item: dict, mode: str) -> str:
    c = PALETTES[mode]
    o = [f'<rect x="1" y="1" width="{PW - 2}" height="{PH - 2}" rx="22" fill="{c["room"]}" '
         f'stroke="{c["line"]}" stroke-width="2"/>']
    o.append(f'<rect x="30" y="30" width="154" height="154" rx="20" fill="{c["sign"]}"/>')
    o.append(f'<g transform="translate(57 57)">{picto(item["picto"], c["sign_ink"])}</g>')
    tx = 220
    o.append(text(item["title"], tx, 76, 40, 800, c["ink"], tracking=-0.01))
    o.append(text(item["note"], PW - 36, 72, 20, 600, c["muted"], "end"))
    lines = wrap(item["desc"], 23, PW - tx - 44, 500)
    assert len(lines) <= 2, (item["key"], lines)
    for i, line in enumerate(lines):
        o.append(text(line, tx, 118 + i * 32, 23, 500, c["muted"]))
    o.append(text(item["stack"], tx, 186, 20, 700, c["blue"]))
    return svg(PW, PH, "".join(o), f'{item["title"]}: {item["desc"]}')


# ------------------------------------------------------------ tools ----

TOOLS = [
    ("Languages", [("typescript", "TypeScript"), ("cplusplus", "C++"), ("python", "Python"),
                   ("kotlin", "Kotlin"), ("openjdk", "Java"), ("dotnet", "C# and .NET")]),
    ("Web", [("nextdotjs", "Next.js"), ("react", "React"), ("tailwindcss", "Tailwind CSS"),
             ("nodedotjs", "Node.js"), ("express", "Express"), ("sanity", "Sanity")]),
    ("Apps and APIs", [("expo", "Expo"), ("android", "Android"), ("springboot", "Spring Boot"),
                       ("fastapi", "FastAPI"), ("firebase", "Firebase")]),
    ("Data", [("postgresql", "PostgreSQL"), ("supabase", "Supabase"), ("mysql", "MySQL"),
              ("mongodb", "MongoDB"), ("googlesheets", "Google Sheets")]),
    ("ML and media", [("scikitlearn", "scikit-learn"), ("googlegemini", "Gemini"),
                      ("ffmpeg", "FFmpeg"), ("streamlit", "Streamlit")]),
    ("Systems", [("linux", "Linux"), ("git", "Git"), ("docker", "Docker"), ("mqtt", "MQTT"),
                 ("n8n", "n8n"), ("sfml", "SFML")]),
]


def tools(mode: str) -> str:
    c = PALETTES[mode]
    row_h, top = 68, 40
    h = top + row_h * (len(TOOLS) - 1) + 32 + 44
    o = [f'<rect x="1" y="1" width="{PW - 2}" height="{h - 2}" rx="22" fill="{c["room"]}" '
         f'stroke="{c["line"]}" stroke-width="2"/>']
    label_w, icon_s, gap_i, gap_item = 230, 26, 12, 34
    for r, (label, items) in enumerate(TOOLS):
        y = top + r * row_h
        if r:
            o.append(f'<path d="M36 {y - 18}H{PW - 36}" stroke="{c["line"]}" stroke-width="1.5"/>')
        o.append(text(label, 40, y + 28, 21, 700, c["ink"]))
        x = 40 + label_w
        for key, name in items:
            o.append(icon(key, x, y + 6, icon_s, c["muted"]))
            o.append(text(name, x + icon_s + gap_i, y + 28, 21, 600, c["muted"]))
            x += icon_s + gap_i + measure(name, 21, 600) + gap_item
        assert x < PW + gap_item, (label, x)
    return svg(PW, h, "".join(o), "Tools I use: " + "; ".join(
        f"{label}: " + ", ".join(n for _, n in items) for label, items in TOOLS))


# ---------------------------------------------------------- contact ----

CONTACT = [
    ("portfolio", "Portfolio", "sameeramjad.xyz"),
    ("linkedin", "LinkedIn", "in/sameeramjd"),
    ("email", "Email", "sameeramjad202@gmail.com"),
]


def contact_icon(kind: str, ink: str) -> str:
    st = f'fill="none" stroke="{ink}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "portfolio":
        return (f'<circle cx="20" cy="20" r="16" {st}/><path d="M4 20H36M20 4C12 12 12 28 20 36'
                f'M20 4C28 12 28 28 20 36" {st}/>')
    if kind == "linkedin":
        return (f'<rect x="3" y="3" width="34" height="34" rx="6" fill="{ink}"/>'
                f'<path d="M12 17V29M12 11.5V11.6M18.5 29V17M18.5 22C18.5 18.5 21 17 23.5 17'
                f'C26.5 17 28 19 28 22.5V29" fill="none" stroke="#FFC530" stroke-width="3.4" stroke-linecap="round"/>')
    return f'<rect x="3" y="7" width="34" height="26" rx="4" {st}/><path d="M5 10L20 22L35 10" {st}/>'


def contact(kind: str, label: str, sub: str) -> str:
    c = PALETTES["dark"]  # signage yellow reads the same on either theme
    w, h = 390, 104
    o = [f'<rect width="{w}" height="{h}" rx="20" fill="{c["sign"]}"/>',
         f'<g transform="translate(28 32)">{contact_icon(kind, c["sign_ink"])}</g>',
         text(label, 88, 50, 27, 800, c["sign_ink"]),
         text(sub, 88, 80, 19, 600, c["sign_ink"], extra=' opacity="0.72"')]
    return svg(w, h, "".join(o), f"{label}: {sub}")


# ------------------------------------------------------------- main ----

def main() -> None:
    for mode in ("dark", "light"):
        write(f"hero-{mode}.svg", hero(mode))
        for item in WORK:
            write(f'work-{item["key"]}-{mode}.svg', panel(item, mode))
        write(f"tools-{mode}.svg", tools(mode))
    for kind, label, sub in CONTACT:
        write(f"contact-{kind}.svg", contact(kind, label, sub))


if __name__ == "__main__":
    main()
