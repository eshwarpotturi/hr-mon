#!/usr/bin/env python3
"""
report.py

Writes the daily stats to ../reports/ so they can be committed to git:
    reports/README.md         overview page: charts, comparisons, highlights
                              (GitHub shows it when you open reports/)
    reports/all_readings.svg  every reading on a time axis (shown in README.md)
    reports/daily_stats.csv   one row per day, rewritten in full each run
    reports/YYYY-MM-DD.md     a short summary per day

Uses the same load_master()/compute_daily_stats() as build_dashboard.py,
so the reports always match the dashboard. Every file is regenerated
from the master dataset on each run, so re-running changes nothing.

Run:
    python3 report.py
"""
import csv
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from build_dashboard import compute_daily_stats, load_master

BASE = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE / "reports"
CSV_PATH = REPORTS_DIR / "daily_stats.csv"
OVERVIEW_PATH = REPORTS_DIR / "README.md"
SCATTER_PATH = REPORTS_DIR / "all_readings.svg"
CHART_DAYS = 30

CSV_COLUMNS = [
    "date", "avg", "min", "max", "resting", "resting_is_real",
    "stdev", "samples", "rolling_avg",
]


def fmt(value, unit=" bpm"):
    return "—" if value is None else f"{value}{unit}"


def delta_vs_prior_week(stats, i, key):
    """'+2.1 vs prior 7-day mean', or '' when there's nothing to compare."""
    current = stats[i][key]
    prior = [s[key] for s in stats[max(0, i - 7):i] if s[key] is not None]
    if current is None or not prior:
        return ""
    diff = round(current - statistics.mean(prior), 1)
    return f" ({diff:+} vs prior {len(prior)}-day mean)"


def write_csv(stats):
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for s in stats:
            writer.writerow([
                s["date"].isoformat() if key == "date"
                else ("" if s[key] is None else s[key])
                for key in CSV_COLUMNS
            ])


def write_day(stats, i):
    s = stats[i]
    resting_kind = "Apple's reading" if s["resting_is_real"] else "estimate"
    lines = [
        f"# Heart rate — {s['date']:%A, %B %d, %Y}",
        "",
        "Heart rate from the `Heart Rate [Min] (bpm)` column.",
        "",
        "| Stat | Value |",
        "|---|---|",
        f"| Average | {fmt(s['avg'])}{delta_vs_prior_week(stats, i, 'avg')} |",
        f"| Min | {fmt(s['min'])} |",
        f"| Max | {fmt(s['max'])} |",
        f"| Resting ({resting_kind}) | {fmt(s['resting'])}"
        f"{delta_vs_prior_week(stats, i, 'resting')} |",
        f"| Std dev | {fmt(s['stdev'], '')} |",
        f"| Samples | {s['samples']} |",
        f"| 7-day rolling avg | {fmt(s['rolling_avg'])} |",
        "",
    ]
    (REPORTS_DIR / f"{s['date']}.md").write_text("\n".join(lines))


def mean(values):
    values = [v for v in values if v is not None]
    return round(statistics.mean(values), 1) if values else None


def compare(value, baseline):
    """'▲ 3.2 higher' / '▼ 1.0 lower' / 'same', or '—' if either is missing."""
    if value is None or baseline is None:
        return "—"
    diff = round(value - baseline, 1)
    if diff == 0:
        return "same"
    return f"▲ {diff} higher" if diff > 0 else f"▼ {abs(diff)} lower"


def label(d):
    return f"{d:%a %d %b}"


def mermaid_chart(title, x_labels, y_label, series):
    """series: list of ("bar"|"line", values). Values must have no None."""
    all_values = [v for _kind, values in series for v in values]
    lo = int(min(all_values) // 10 * 10) - 10
    hi = int(max(all_values) // 10 * 10) + 20
    axis = ", ".join(f'"{x}"' for x in x_labels)
    lines = ["```mermaid", "xychart-beta", f'    title "{title}"',
             f"    x-axis [{axis}]", f'    y-axis "{y_label}" {max(lo, 0)} --> {hi}']
    for kind, values in series:
        lines.append(f"    {kind} [{', '.join(str(v) for v in values)}]")
    lines.append("```")
    return "\n".join(lines)


def write_scatter_svg(rows, start_day):
    """Every HR reading from start_day on, as a dot at its real time, plus
    Apple's resting reading as a line across its day. Pure stdlib SVG."""
    readings = [(ts, hr) for ts, hr, _ in rows if hr is not None and ts.date() >= start_day]
    resting = [(ts, rhr) for ts, _, rhr in rows if rhr is not None and ts.date() >= start_day]
    width, height = 1000, 360
    left, right, top, bottom = 50, 20, 40, 40
    plot_w, plot_h = width - left - right, height - top - bottom

    t0 = datetime.combine(start_day, datetime.min.time())
    t1 = datetime.combine(readings[-1][0].date(), datetime.min.time()) + timedelta(days=1)
    span = (t1 - t0).total_seconds()
    values = [hr for _, hr in readings] + [rhr for _, rhr in resting]
    lo = max(int(min(values) // 10 * 10) - 10, 0)
    hi = int(max(values) // 10 * 10) + 20

    def x(ts):
        return round(left + (ts - t0).total_seconds() / span * plot_w, 1)

    def y(bpm):
        return round(top + (hi - bpm) / (hi - lo) * plot_h, 1)

    title = "Every heart-rate reading"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="sans-serif" font-size="11">',
        f"<title>{title}</title>",
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{left}" y="20" font-size="14" font-weight="bold" fill="#222">{title}</text>',
        f'<text x="{left - 36}" y="{top - 8}" fill="#555">bpm</text>',
    ]
    for bpm in range((lo + 19) // 20 * 20, hi + 1, 20):
        out += [f'<line x1="{left}" x2="{width - right}" y1="{y(bpm)}" y2="{y(bpm)}" stroke="#e5e5e5"/>',
                f'<text x="{left - 6}" y="{y(bpm) + 4}" text-anchor="end" fill="#555">{bpm}</text>']
    days = (t1 - t0).days
    step = 1 if days <= 14 else 2
    for i in range(days + 1):
        day = t0 + timedelta(days=i)
        out.append(f'<line x1="{x(day)}" x2="{x(day)}" y1="{top}" y2="{top + plot_h}" stroke="#d0d0d0"/>')
        if i < days and i % step == 0:
            mid = x(day + timedelta(hours=12))
            out.append(f'<text x="{mid}" y="{top + plot_h + 16}" text-anchor="middle" '
                       f'fill="#555">{day:%d %b}</text>')
    for ts, rhr in resting:
        day = datetime.combine(ts.date(), datetime.min.time())
        out.append(f'<line x1="{x(day)}" x2="{x(day + timedelta(days=1))}" y1="{y(rhr)}" '
                   f'y2="{y(rhr)}" stroke="#e8590c" stroke-width="2"/>')
    out.append('<g fill="#2a6fdb" fill-opacity="0.45">')
    out += [f'<circle cx="{x(ts)}" cy="{y(hr)}" r="2"/>' for ts, hr in readings]
    out.append("</g>")
    lx = width - right - 260
    out += [
        f'<circle cx="{lx}" cy="16" r="3" fill="#2a6fdb"/>',
        f'<text x="{lx + 8}" y="20" fill="#333">Heart rate reading</text>',
        f'<line x1="{lx + 125}" x2="{lx + 141}" y1="16" y2="16" stroke="#e8590c" stroke-width="2"/>',
        f'<text x="{lx + 147}" y="20" fill="#333">Apple resting HR</text>',
        "</svg>", "",
    ]
    SCATTER_PATH.write_text("\n".join(out))


def hourly_averages(rows, day):
    by_hour = defaultdict(list)
    for ts, hr, _rhr in rows:
        if hr is not None and ts.date() == day:
            by_hour[ts.hour].append(hr)
    return {h: round(statistics.mean(v), 1) for h, v in sorted(by_hour.items())}


def week_table(hr_days):
    """Last 7 days vs the 7 before them."""
    this_week, last_week = hr_days[-7:], hr_days[-14:-7]
    lines = [
        f"| | This week ({label(this_week[0]['date'])} – {label(this_week[-1]['date'])}) "
        f"| Previous week | Change |",
        "|---|---|---|---|",
    ]
    for name, key, agg in [
        ("Average HR", "avg", mean),
        ("Resting HR", "resting", mean),
        ("Lowest reading", "min", min),
        ("Highest reading", "max", max),
        ("Variability (std dev)", "stdev", mean),
    ]:
        now = agg([s[key] for s in this_week if s[key] is not None])
        before = (agg([s[key] for s in last_week if s[key] is not None])
                  if last_week else None)
        lines.append(f"| {name} | {now} | {before if before is not None else '—'} "
                     f"| {compare(now, before)} |")
    if len(last_week) < 7:
        missing = 14 - len(hr_days)
        lines += ["", f"_Previous week has {len(last_week)} of 7 days so far; "
                      f"the comparison is complete after {missing} more day(s) of data._"]
    return "\n".join(lines)


def write_overview(stats, rows):
    hr_days = [s for s in stats if s["avg"] is not None]
    out = ["# Heart rate report", ""]
    if not hr_days:
        OVERVIEW_PATH.write_text("\n".join(out + ["No heart-rate data yet.", ""]))
        return

    latest = hr_days[-1]
    earlier = hr_days[:-1]
    first_ts = min(ts for ts, hr, _ in rows if hr is not None)
    last_ts = max(ts for ts, hr, _ in rows if hr is not None)
    overall_avg = mean(s["avg"] for s in hr_days)
    overall_resting = mean(s["resting"] for s in hr_days)

    out += [
        f"**Data from {first_ts:%d %b %Y} to {last_ts:%d %b %Y, %H:%M}** · "
        f"{len(hr_days)} days · {sum(s['samples'] for s in hr_days):,} readings · "
        "heart rate from the `Heart Rate [Min] (bpm)` column.",
        "",
        f"## Latest day: {latest['date']:%A %d %B}",
        "",
        "| | This day | Your usual (average of previous days) | Compared with usual |",
        "|---|---|---|---|",
    ]
    for name, key in [("Average HR", "avg"), ("Resting HR", "resting"),
                      ("Lowest reading", "min"), ("Highest reading", "max"),
                      ("Variability (std dev)", "stdev")]:
        baseline = mean(s[key] for s in earlier) if earlier else None
        out.append(f"| {name} | {latest[key]} | {baseline if baseline is not None else '—'} "
                   f"| {compare(latest[key], baseline)} |")
    resting_kind = ("Apple's own resting reading" if latest["resting_is_real"]
                    else "an estimate (no Apple reading that day)")
    out += ["", f"Resting HR for this day is {resting_kind}. "
                f"{latest['samples']} readings. "
                f"[Full day report]({latest['date']}.md)", ""]

    hourly = hourly_averages(rows, latest["date"])
    if len(hourly) >= 2:
        out += [mermaid_chart(f"{label(latest['date'])}: average HR by hour",
                              [f"{h:02d}h" for h in hourly], "bpm",
                              [("bar", list(hourly.values()))]), ""]

    out += ["## This week vs last week", "", week_table(hr_days), ""]

    shown = hr_days[-CHART_DAYS:]
    x = [f"{s['date']:%d %b}" for s in shown]
    write_scatter_svg(rows, shown[0]["date"])
    out += [
        "## Trends", "",
        "**Every reading**: each dot is one heart-rate sample at its real time; "
        "gaps are when the watch wasn't recording. The orange line is Apple's "
        "resting HR for that day.", "",
        f"![Every heart-rate reading]({SCATTER_PATH.name})", "",
        "**Daily average** (bars) and **7-day rolling average** (line).", "",
        mermaid_chart("Daily average heart rate", x, "bpm",
                      [("bar", [s["avg"] for s in shown]),
                       ("line", [s["rolling_avg"] for s in shown])]), "",
        "**Daily range**: highest reading (top line), average (middle), "
        "lowest reading (bottom).", "",
        mermaid_chart("Daily range", x, "bpm",
                      [("line", [s["max"] for s in shown]),
                       ("line", [s["avg"] for s in shown]),
                       ("line", [s["min"] for s in shown])]), "",
    ]
    resting_days = [s for s in shown if s["resting"] is not None]
    if len(resting_days) >= 2:
        out += [
            "**Resting heart rate.** A lower resting HR over time usually "
            "goes with better fitness and recovery; short spikes often follow "
            "poor sleep, stress, illness or alcohol.", "",
            mermaid_chart("Resting heart rate", [f"{s['date']:%d %b}" for s in resting_days],
                          "bpm", [("line", [s["resting"] for s in resting_days])]), "",
        ]

    def pick(key, fn):
        candidates = [s for s in hr_days if s[key] is not None]
        return fn(candidates, key=lambda s: s[key]) if candidates else None

    highlights = [
        ("Lowest resting HR", pick("resting", min), "resting"),
        ("Highest resting HR", pick("resting", max), "resting"),
        ("Calmest day (lowest average)", pick("avg", min), "avg"),
        ("Busiest day (highest average)", pick("avg", max), "avg"),
        ("Highest single reading", pick("max", max), "max"),
        ("Most variable day", pick("stdev", max), "stdev"),
    ]
    out += ["## Highlights", "", "| | Day | Value |", "|---|---|---|"]
    for name, day, key in highlights:
        if day:
            unit = "" if key == "stdev" else " bpm"
            out.append(f"| {name} | [{label(day['date'])}]({day['date']}.md) "
                       f"| {day[key]}{unit} |")

    out += ["", "## Every day", "",
            f"Compared with your overall average of **{overall_avg} bpm** "
            f"(resting **{overall_resting} bpm**). Newest first.", "",
            "| Day | Avg | vs overall | Resting | vs overall | Min | Max | Std dev | Readings |",
            "|---|---|---|---|---|---|---|---|---|"]
    for s in reversed(hr_days):
        resting = f"{s['resting']}" + ("" if s["resting_is_real"] else "~")
        out.append(
            f"| [{label(s['date'])}]({s['date']}.md) | {s['avg']} "
            f"| {compare(s['avg'], overall_avg)} | {resting} "
            f"| {compare(s['resting'], overall_resting)} | {s['min']} | {s['max']} "
            f"| {s['stdev']} | {s['samples']} |")

    out += [
        "", "`~` = resting HR estimated (no Apple reading that day). ",
        "", "<details><summary>What the numbers mean</summary>", "",
        "- **Average HR**: mean of all readings that day.",
        "- **Resting HR**: Apple's once-a-day resting value; if missing, the mean "
        "of that day's lowest 10% of readings.",
        "- **Lowest / highest reading**: extremes across the day's readings.",
        "- **Variability (std dev)**: how much HR moved around during the day; "
        "higher usually means more activity.",
        "- **7-day rolling average**: average of the last 7 days' averages; "
        "smooths out single-day noise.",
        "- **Readings**: Apple Watch samples HR every few minutes at rest, more "
        "often when active, so more readings usually means more wear time or activity.",
        "", "Not medical advice.", "", "</details>", "",
        "Raw numbers: [daily_stats.csv](daily_stats.csv)", "",
    ]
    OVERVIEW_PATH.write_text("\n".join(out))


def main():
    rows = load_master()
    stats = compute_daily_stats(rows)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(stats)
    write_overview(stats, rows)
    for i in range(len(stats)):
        write_day(stats, i)
    print(f"Reports written to {REPORTS_DIR} ({len(stats)} days)")


if __name__ == "__main__":
    main()
