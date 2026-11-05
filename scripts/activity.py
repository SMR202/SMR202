"""Renders the contribution panel (assets/activity-*.svg).

Runs every day in .github/workflows/activity.yml. Locally, without a token,
`python scripts/activity.py --placeholder` draws an empty grid.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.request

from kit import PALETTES, measure, svg, text, write

LOGIN = os.environ.get("PROFILE_LOGIN", "SMR202")
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""


def fetch(token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-activity-panel"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        payload = json.load(res)
    if "errors" in payload:
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def placeholder() -> dict:
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)  # a Sunday
    weeks, day = [], start
    while day <= today:
        week = []
        for _ in range(7):
            if day <= today:
                week.append({"date": day.isoformat(), "contributionCount": 0, "contributionLevel": "NONE"})
            day += dt.timedelta(days=1)
        weeks.append({"contributionDays": week})
    return {"totalContributions": None, "weeks": weeks}


def streaks(days: list[dict]) -> tuple[int, int]:
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for n in counts:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    tail = counts[:-1] if counts and counts[-1] == 0 else counts  # today may still be empty
    for n in reversed(tail):
        if not n:
            break
        current += 1
    return current, longest


def plural(n: int, word: str) -> str:
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def render(cal: dict, mode: str, updated: dt.date) -> str:
    c = PALETTES[mode]
    W, H = 1200, 344
    cell, gap = 15.5, 4.5
    step = cell + gap
    gx, gy = 96, 134
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]

    o = [f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="{c["card"]}" '
         f'stroke="{c["line"]}" stroke-width="2"/>']

    total = cal["totalContributions"]
    if total is None:
        o.append(text("Contribution activity", 40, 72, 30, "x700", c["ink"], tracking=-0.01))
        o.append(text("Waiting for the first daily refresh", W - 40, 70, 20, "t500", c["muted"], "end"))
    else:
        o.append(text(f"{plural(total, 'contribution')} in the last year", 40, 72, 30, "x700", c["ink"],
                      tracking=-0.01))
        current, longest = streaks(days)
        x = W - 40
        for label, value in (("Longest streak", plural(longest, "day")), ("Current streak", plural(current, "day"))):
            o.append(text(value, x, 70, 20, "t700", c["ink"], "end"))
            x -= measure(value, 20, "t700") + 10
            o.append(text(label, x, 70, 20, "t500", c["muted"], "end"))
            x -= measure(label, 20, "t500") + 36

    # weekday labels
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(text(name, 40, gy + row * step + 13, 16, "t500", c["muted"]))

    last_month, last_x = None, -99
    css = []
    for col, week in enumerate(cal["weeks"]):
        x = gx + col * step
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month:
            if col and x - last_x > 3 * step and col < len(cal["weeks"]) - 1:
                o.append(text(first.strftime("%b"), x, gy - 14, 16, "t500", c["muted"]))
                last_x = x
            last_month = first.month
        for d in week["contributionDays"]:
            row = (dt.date.fromisoformat(d["date"]).weekday() + 1) % 7  # Sunday first
            lvl = LEVELS.get(d["contributionLevel"], 0)
            o.append(f'<rect x="{x:.1f}" y="{gy + row * step:.1f}" width="{cell}" height="{cell}" rx="3.5" '
                     f'fill="{c["heat"][lvl]}"><title>{d["date"]}: {d["contributionCount"]}</title></rect>')

    # today, outlined in tangerine
    last = days[-1]
    col = len(cal["weeks"]) - 1
    row = (dt.date.fromisoformat(last["date"]).weekday() + 1) % 7
    tx, ty = gx + col * step, gy + row * step
    o.append(f'<rect class="today" x="{tx - 3:.1f}" y="{ty - 3:.1f}" width="{cell + 6}" height="{cell + 6}" '
             f'rx="5.5" fill="none" stroke="{c["tangerine"]}" stroke-width="2.5"/>')
    css.append(".today{animation:today 2.4s ease-in-out infinite}"
               "@keyframes today{0%,100%{opacity:1}50%{opacity:.25}}"
               "@media (prefers-reduced-motion: reduce){.today{animation:none}}")

    # legend and freshness
    fy = H - 34
    o.append(text("Less", 96, fy, 17, "t500", c["muted"]))
    lx = 96 + measure("Less", 17, "t500") + 12
    for lvl in range(5):
        o.append(f'<rect x="{lx:.1f}" y="{fy - 13}" width="15" height="15" rx="3.5" fill="{c["heat"][lvl]}"/>')
        lx += 20
    o.append(text("More", lx + 6, fy, 17, "t500", c["muted"]))
    o.append(text("Today", lx + 70 + 24, fy, 17, "t500", c["muted"]))
    o.append(f'<rect x="{lx + 64:.1f}" y="{fy - 14}" width="17" height="17" rx="4.5" fill="none" '
             f'stroke="{c["tangerine"]}" stroke-width="2.5"/>')
    note = ("Refreshed daily by a GitHub Action" if total is None
            else f"Refreshed daily by a GitHub Action, last on {updated.day} {updated:%b %Y}")
    o.append(text(note, W - 40, fy, 17, "t500", c["muted"], "end"))

    summary = ("Contribution activity, waiting for the first refresh" if total is None
               else f"{plural(total, 'contribution')} in the last year")
    return svg(W, H, "".join(o), summary, "".join(css))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--placeholder", action="store_true")
    args = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if args.placeholder:
        cal = placeholder()
    elif token:
        cal = fetch(token)
    else:
        raise SystemExit("Set GITHUB_TOKEN, or pass --placeholder.")
    updated = dt.datetime.now(dt.timezone.utc).date()
    for mode in ("dark", "light"):
        write(f"activity-{mode}.svg", render(cal, mode, updated))


if __name__ == "__main__":
    main()
