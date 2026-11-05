"""Builds the profile artwork in assets/ (dark and light versions).

    pip install -r scripts/requirements.txt
    python scripts/build_assets.py

The art is a flow field: hundreds of lines follow a noise field and stop
just before they touch each other or the type. The activity panel is drawn
separately by scripts/activity.py, which a GitHub Action runs every night.
"""

from __future__ import annotations

import math
import random
import sys

from flow import Mask, Noise, pack, smooth_path
from kit import PALETTES, face, icon, measure, num, svg, text, wrap, write

REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def ink_mix(c: dict, names: list[tuple[str, float]]) -> list[tuple[str, float]]:
    return [(c[n], w) for n, w in names]


def draw_lines(lines, c, *, sweep: float = 0.0, sweep_w: float = 1200, dur: float = 1.4,
               base_delay: float = 0.1, cls: str = "d") -> tuple[str, str]:
    """SVG for packed lines. With sweep > 0 they draw in from left to right."""
    out = []
    for i, ln in enumerate(lines):
        d = smooth_path(ln.pts)
        w = num(ln.width)
        if ln.dotted:
            gap = num(ln.width * 1.9)
            attrs = f'stroke-dasharray="0 {gap}"'
            anim = "f"
        else:
            attrs = 'pathLength="1" stroke-dasharray="1"'
            anim = cls
        delay = ""
        if sweep:
            x0 = min(p[0] for p in ln.pts)
            delay = f' style="animation-delay:{base_delay + sweep * x0 / sweep_w:.2f}s"'
        out.append(f'<path class="{anim}" d="{d}" stroke="{ln.color}" stroke-width="{w}" {attrs}{delay}/>')
    css = ""
    if sweep:
        css = (f".{cls}{{animation:{cls} {dur}s cubic-bezier(.3,.6,.2,1) both}}"
               f"@keyframes {cls}{{0%{{stroke-dashoffset:1;opacity:0}}1%{{opacity:1}}100%{{stroke-dashoffset:0}}}}"
               ".f{animation:f .9s ease-out both}@keyframes f{0%{opacity:0}100%{opacity:1}}")
    return (f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">{"".join(out)}</g>', css)


# ---------------------------------------------------------------- hero ----

HW, HH = 1200, 600
NAME = [("Sameer", 60, 292), ("Amjad", 60, 444)]
NAME_SIZE = 150
TAG = [("Software engineer in Islamabad, building real-time", 64, 514),
       ("systems, AI pipelines and websites people use.", 64, 548)]


def hero(mode: str, seed: int = 7) -> str:
    c = PALETTES[mode]
    display = face("x800")
    mask = Mask(HW, HH)
    # Each line of type gets its own clear band, so the field wraps the block
    # and steps in and out with the different line lengths.
    cap = display.cap * NAME_SIZE / display.upem
    for word, x, y in NAME:
        w = display.measure(word, NAME_SIZE, -0.02)
        mask.rect(0, y - cap - 6, x + w + 6, y + 10)
    for line, x, y in TAG:
        w = measure(line, 26, "t500")
        mask.rect(0, y - 26, x + w + 4, HH)
    mask.rect(0, NAME[0][2], 120, HH)  # keep the left edge under the name calm
    mask.grow(20)

    noise = Noise(seed)

    def angle(x, y):
        n = noise(x * 0.0021, y * 0.0021) + 0.5 * noise(x * 0.006 + 40, y * 0.006 + 40)
        return n * math.pi * 1.25 - 0.35

    lines = pack(HW, HH, angle, seed=seed, mask=mask,
                 colors=ink_mix(c, [("tangerine", 0.25), ("marigold", 0.22), ("rose", 0.2),
                                    ("jade", 0.15), ("lilac", 0.08), ("ink", 0.10)]),
                 widths=[(4, 0.32), (7, 0.30), (11, 0.24), (15, 0.14)],
                 spacing=9, gap=4.2, step=2.5, min_len=34, max_len=640, margin=6, dotted_share=0.06)

    art, css = draw_lines(lines, c, sweep=1.6, dur=1.5)

    # sparks: light travelling along a few of the longest lines
    rnd = random.Random(seed)
    long_lines = sorted((ln for ln in lines if not ln.dotted and ln.width >= 7), key=lambda l: -l.length)[:40]
    rnd.shuffle(long_lines)
    sparks = []
    for ln in long_lines[:22]:
        period = rnd.uniform(4.5, 8.0)
        delay = rnd.uniform(1.6, 1.6 + period)
        sparks.append(f'<path class="k" d="{smooth_path(ln.pts)}" stroke-width="{num(ln.width * 0.42)}" '
                      f'pathLength="1" style="animation-duration:{period:.1f}s;animation-delay:{delay:.1f}s"/>')
    css += (".k{stroke-dasharray:.07 1.2;stroke-dashoffset:.07;animation:k linear infinite both}"
            "@keyframes k{0%{stroke-dashoffset:.07}100%{stroke-dashoffset:-1.13}}")
    spark_g = (f'<g fill="none" stroke="{c["spark"]}" stroke-opacity="0.9" stroke-linecap="round">'
               f'{"".join(sparks)}</g>')

    body = [art, spark_g]
    for word, x, y in NAME:
        body.append(text(word, x, y, NAME_SIZE, "x800", c["ink"], tracking=-0.02))
    for line, x, y in TAG:
        body.append(text(line, x, y, 26, "t500", c["muted"]))
    return svg(HW, HH, "".join(body),
               "Sameer Amjad. Software engineer in Islamabad, building real-time systems, "
               "AI pipelines and websites people use.", css + REDUCED)


# ------------------------------------------------------------ cards ----
# Each cover is the same line packer driven by a field that suits the work.

CW, CH, COVER = 600, 470, 236


def field(kind: str, seed: int):
    n = Noise(seed)
    W, H = CW, COVER
    if kind == "converge":
        cx, cy = W * 0.68, H * 0.52
        return lambda x, y: math.atan2(cy - y, cx - x) + 1.2 + 0.35 * n(x * 0.01, y * 0.01)
    if kind == "waves":
        return lambda x, y: 0.85 * math.sin(x * 0.018 + 2.4 * n(x * 0.004, y * 0.012))
    if kind == "organic":
        return lambda x, y: n(x * 0.011, y * 0.011) * math.tau * 1.4
    if kind == "blocks":
        return lambda x, y: round(n(x * 0.006, y * 0.006) * 4) * math.pi / 2
    if kind == "orbit":
        cx, cy = W * 0.5, H * 0.55
        return lambda x, y: math.atan2(y - cy, x - cx) + math.pi / 2 + 0.18 * n(x * 0.02, y * 0.02)
    if kind == "mirror":
        def f(x, y):
            a = n(abs(x - W / 2) * 0.008, y * 0.008) * math.tau
            return a if x >= W / 2 else math.pi - a
        return f
    if kind == "tree":
        return lambda x, y: (-math.pi / 2 + 1.1 * math.atan((x - W / 2) / (H - y + 60))
                             + 0.25 * n(x * 0.01, y * 0.01))
    if kind == "circuit":
        return lambda x, y: round(n(x * 0.007, y * 0.007) * 8) * math.pi / 4
    raise KeyError(kind)


WORK = [
    dict(key="turn", field="converge", inks=["tangerine", "marigold", "ink"], seed=11,
         title="TURN", role="Final-year project", url="https://github.com/SMR202/turn-indoor-navigation",
         desc="Indoor navigation for malls that works without beacons. I build the positioning: "
              "step detection, heading and a particle filter that knows the floor plan.",
         stack="Android, sensor fusion, Python"),
    dict(key="lumen", field="waves", inks=["rose", "lilac", "ink"], seed=5,
         title="Lumen", role="Team project",
         url="https://github.com/ZakiNabeel/AI-System-for-Live-and-Recorded-Online-Video-Understanding-and-Summarization",
         desc="Watches a live stream or a recorded video, then transcribes it, reads the frames "
              "and answers questions about it through a ten-stage pipeline.",
         stack="Python, FastAPI, Whisper, Gemini, Next.js"),
    dict(key="neurozehn", field="organic", inks=["lilac", "rose", "jade"], seed=3,
         title="NeuroZehn", role="Client", url="https://github.com/SMR202/Neurosphere-Global",
         desc="A 61-page site for a brain-health institute, with Urdu right-to-left previews "
              "and every claim traced back to the client's own sources.",
         stack="Next.js, TypeScript, Tailwind CSS"),
    dict(key="clients", field="blocks", inks=["tangerine", "marigold", "rose", "jade", "lilac"], seed=8,
         title="Local business sites", role="Freelance", url="https://www.sameeramjad.xyz",
         desc="Twenty-plus sites and pitch builds for cafés, salons, bakeries, a furniture maker, "
              "a school and a collector-car marketplace in Islamabad.",
         stack="Next.js, Sanity, Google Sheets, Vercel"),
    dict(key="aircontrolx", field="orbit", inks=["marigold", "tangerine", "ink"], seed=2,
         title="AirControlX", role="Operating systems", url="https://github.com/SMR202/AirControlX",
         desc="Air traffic control for three runways, with arrivals, emergencies and violation "
              "notices, run on POSIX threads and Unix pipes and drawn in SFML.",
         stack="C++, pthreads, IPC, SFML"),
    dict(key="twin", field="mirror", inks=["jade", "marigold", "ink"], seed=4,
         title="Twin sync research", role="Research", url="https://github.com/SMR202/dt-mqtt-resilience",
         desc="How MQTT QoS levels and edge buffering change freshness, delivery and recovery "
              "when a cloud digital twin loses its connection.",
         stack="MQTT, edge computing, cloud"),
    dict(key="merkle", field="tree", inks=["jade", "lilac", "ink"], seed=6,
         title="Integrity checks", role="Data structures",
         url="https://github.com/SMR202/IntegrityVerificationSystem",
         desc="SHA-256 Merkle trees over a million product reviews. Finds edits, deletions and "
              "insertions, and verifies proofs in under 100 ms.",
         stack="Python, SHA-256, CustomTkinter"),
    dict(key="parser", field="circuit", inks=["tangerine", "rose", "ink"], seed=9,
         title="LL(1) parser", role="Compilers", url="https://github.com/SMR202/LL-1-Parser",
         desc="Reads a grammar, removes left recursion, left-factors it, builds FIRST and FOLLOW "
              "sets and the parse table, then parses input with error handling.",
         stack="C++17"),
]


def card(item: dict, mode: str) -> str:
    c = PALETTES[mode]
    weights = [0.42, 0.33, 0.25] if len(item["inks"]) == 3 else [1 / len(item["inks"])] * len(item["inks"])
    lines = pack(CW, COVER, field(item["field"], item["seed"]), seed=item["seed"],
                 colors=ink_mix(c, list(zip(item["inks"], weights))),
                 widths=[(3, 0.34), (5, 0.32), (8, 0.22), (11, 0.12)],
                 spacing=8, gap=3.2, step=2.0, min_len=24, max_len=420, margin=18, dotted_share=0.05)
    art, css = draw_lines(lines, c, sweep=0.9, sweep_w=CW, dur=1.2, base_delay=0.05)

    body = [f'<defs><clipPath id="cv"><rect x="1" y="1" width="{CW - 2}" height="{COVER}" rx="23"/></clipPath></defs>',
            f'<rect x="1" y="1" width="{CW - 2}" height="{CH - 2}" rx="24" fill="{c["card"]}" '
            f'stroke="{c["line"]}" stroke-width="2"/>',
            f'<g clip-path="url(#cv)">{art}</g>',
            f'<path d="M1 {COVER}H{CW - 1}" stroke="{c["line"]}" stroke-width="2"/>']
    x, y = 34, COVER + 62
    body.append(text(item["title"], x, y, 31, "x700", c["ink"], tracking=-0.01))
    lines_ = wrap(item["desc"], 21, CW - 2 * x, "t400")
    assert len(lines_) <= 3, (item["key"], lines_)
    for i, ln in enumerate(lines_):
        body.append(text(ln, x, y + 42 + i * 30, 21, "t400", c["muted"]))
    body.append(text(item["stack"], x, CH - 34, 18, "t600", c["ink"]))
    body.append(text(item["role"], CW - x, CH - 34, 18, "t500", c["muted"], "end"))
    return svg(CW, CH, "".join(body), f'{item["title"]}. {item["desc"]}', css + REDUCED)


# ------------------------------------------------------------ tools ----

TOOLS = [
    ("Languages", "tangerine", [("typescript", "TypeScript"), ("cplusplus", "C++"), ("python", "Python"),
                                ("kotlin", "Kotlin"), ("openjdk", "Java"), ("dotnet", "C#")]),
    ("Web", "marigold", [("nextdotjs", "Next.js"), ("react", "React"), ("tailwindcss", "Tailwind CSS"),
                         ("nodedotjs", "Node.js"), ("express", "Express"), ("sanity", "Sanity")]),
    ("Apps and APIs", "rose", [("expo", "Expo"), ("android", "Android"), ("springboot", "Spring Boot"),
                               ("fastapi", "FastAPI"), ("firebase", "Firebase")]),
    ("Data", "jade", [("postgresql", "PostgreSQL"), ("supabase", "Supabase"), ("mysql", "MySQL"),
                      ("mongodb", "MongoDB"), ("googlesheets", "Google Sheets")]),
    ("ML and media", "lilac", [("scikitlearn", "scikit-learn"), ("googlegemini", "Gemini"),
                               ("ffmpeg", "FFmpeg"), ("streamlit", "Streamlit")]),
    ("Systems", "ink", [("linux", "Linux"), ("git", "Git"), ("docker", "Docker"), ("mqtt", "MQTT"),
                        ("n8n", "n8n"), ("sfml", "SFML")]),
]


def tools(mode: str) -> str:
    c = PALETTES[mode]
    W, row_h, top = 1200, 66, 44
    h = top + row_h * (len(TOOLS) - 1) + 30 + 44
    o = [f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="24" fill="{c["card"]}" '
         f'stroke="{c["line"]}" stroke-width="2"/>']
    label_w, icon_s, gap_i, gap_item = 236, 24, 11, 34
    for r, (label, ink, items) in enumerate(TOOLS):
        y = top + r * row_h
        if r:
            o.append(f'<path d="M40 {y - 19}H{W - 40}" stroke="{c["line"]}" stroke-width="1.5"/>')
        o.append(f'<rect x="40" y="{y + 7}" width="8" height="22" rx="4" fill="{c[ink]}"/>')
        o.append(text(label, 62, y + 26, 21, "t700", c["ink"]))
        x = 40 + label_w
        for key, name in items:
            o.append(icon(key, x, y + 6, icon_s, c["muted"]))
            o.append(text(name, x + icon_s + gap_i, y + 26, 21, "t500", c["muted"]))
            x += icon_s + gap_i + measure(name, 21, "t500") + gap_item
        assert x < W + gap_item, (label, x)
    return svg(W, h, "".join(o), "Tools I use. " + " ".join(
        f"{label}: " + ", ".join(n for _, n in items) + "." for label, _, items in TOOLS))


# ---------------------------------------------------------- contact ----

CONTACT = [
    ("email", "Email", False),
    ("linkedin", "LinkedIn", False),
    ("portfolio", "Portfolio", False),
    ("resume", "Resume", True),
]


def contact_icon(kind: str, col: str) -> str:
    st = f'fill="none" stroke="{col}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "portfolio":
        return (f'<circle cx="12" cy="12" r="10" {st}/>'
                f'<path d="M2 12H22M12 2C7 7 7 17 12 22M12 2C17 7 17 17 12 22" {st}/>')
    if kind == "linkedin":
        return (f'<rect x="2" y="2" width="20" height="20" rx="4" {st}/>'
                f'<path d="M7.5 10.5V16.5M7.5 7.4V7.5M11.5 16.5V10.5M11.5 13C11.5 11.3 12.7 10.4 14 10.4'
                f'C15.6 10.4 16.5 11.4 16.5 13.2V16.5" {st}/>')
    if kind == "resume":
        return (f'<path d="M6 2H14L19 7V20C19 21.1 18.1 22 17 22H6C4.9 22 4 21.1 4 20V4C4 2.9 4.9 2 6 2Z" {st}/>'
                f'<path d="M14 2V7H19M8 13H15M8 17H13" {st}/>')
    return f'<rect x="2" y="4" width="20" height="16" rx="3" {st}/><path d="M3 6L12 13L21 6" {st}/>'


def contact(kind: str, label: str, filled: bool, mode: str) -> str:
    c = PALETTES[mode]
    size = 22
    w = int(28 + 24 + 12 + measure(label, size, "t600") + 30)
    h = 60
    if filled:
        bg, fg, stroke = c["ink"], c["page"], c["ink"]
    else:
        bg, fg, stroke = c["page"], c["ink"], c["line"]
    o = [f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="{(h - 3) / 2}" fill="{bg}" '
         f'stroke="{stroke}" stroke-width="2"/>',
         f'<g transform="translate(28 18)">{contact_icon(kind, fg)}</g>',
         text(label, 64, 38, size, "t600", fg)]
    return svg(w, h, "".join(o), label)


def main() -> None:
    only = sys.argv[1:]
    for mode in ("dark", "light"):
        if not only or "hero" in only:
            write(f"hero-{mode}.svg", hero(mode))
        if not only or "cards" in only:
            for item in WORK:
                write(f'work-{item["key"]}-{mode}.svg', card(item, mode))
        if not only or "tools" in only:
            write(f"tools-{mode}.svg", tools(mode))
        if not only or "contact" in only:
            for kind, label, filled in CONTACT:
                write(f"contact-{kind}-{mode}.svg", contact(kind, label, filled, mode))


if __name__ == "__main__":
    main()
