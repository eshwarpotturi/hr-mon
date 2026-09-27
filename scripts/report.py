#!/usr/bin/env python3
"""
report.py

Writes the daily stats to ../reports/ so they can be committed to git:
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
from pathlib import Path

from build_dashboard import compute_daily_stats, load_master

BASE = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE / "reports"
CSV_PATH = REPORTS_DIR / "daily_stats.csv"

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


def main():
    stats = compute_daily_stats(load_master())
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(stats)
    for i in range(len(stats)):
        write_day(stats, i)
    print(f"Reports written to {REPORTS_DIR} ({len(stats)} days)")


if __name__ == "__main__":
    main()
