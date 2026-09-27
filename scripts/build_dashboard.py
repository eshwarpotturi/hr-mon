#!/usr/bin/env python3
"""
build_dashboard.py

Reads ../data/heart_rate_master.csv, computes daily trend stats
(average / min / max / resting HR / 7-day rolling average / variability),
and writes a fully self-contained ../dashboard/index.html (inline SVG
charts, no external JS/CSS libraries — works fully offline).

Resting HR: uses Apple's own "Resting Heart Rate" reading for that day
when the export included it (real Apple-computed value). Falls back to
an approximation (mean of the lowest ~10% of that day's Heart Rate
samples) only for days where no real resting-HR reading is present.
Each day's row is labeled so you always know which kind you're looking at.

Run:
    python3 build_dashboard.py
"""
import csv
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MASTER_PATH = BASE / "data" / "heart_rate_master.csv"
DASHBOARD_PATH = BASE / "dashboard" / "index.html"

MAX_DAYS_SHOWN = 30


def load_master():
    rows = []
    if not MASTER_PATH.exists():
        return rows
    with MASTER_PATH.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            except (ValueError, KeyError):
                continue
            hr_raw = (row.get("heart_rate") or "").strip()
            rhr_raw = (row.get("resting_heart_rate") or "").strip()
            hr = int(round(float(hr_raw))) if hr_raw else None
            rhr = int(round(float(rhr_raw))) if rhr_raw else None
            if hr is None and rhr is None:
                continue
            rows.append((ts, hr, rhr))
    rows.sort(key=lambda r: r[0])
    return rows


def resting_proxy(values):
    """Approximate resting HR when Apple's own reading isn't present:
    mean of the lowest 10% of that day's HR samples (minimum 3 samples)."""
    if not values:
        return None
    n = max(3, len(values) // 10)
    lowest = sorted(values)[:n]
    return round(statistics.mean(lowest), 1)


def compute_daily_stats(rows):
    hr_by_day = defaultdict(list)
    rhr_by_day = defaultdict(list)
    for ts, hr, rhr in rows:
        d = ts.date()
        if hr is not None:
            hr_by_day[d].append(hr)
        if rhr is not None:
            rhr_by_day[d].append(rhr)

    days = sorted(set(hr_by_day.keys()) | set(rhr_by_day.keys()))
    stats = []
    for d in days:
        hr_values = hr_by_day.get(d, [])
        rhr_values = rhr_by_day.get(d, [])

        if rhr_values:
            resting_value = round(statistics.mean(rhr_values), 1)
            resting_is_real = True
        elif hr_values:
            resting_value = resting_proxy(hr_values)
            resting_is_real = False
        else:
            resting_value = None
            resting_is_real = False

        stats.append({
            "date": d,
            "avg": round(statistics.mean(hr_values), 1) if hr_values else None,
            "min": min(hr_values) if hr_values else None,
            "max": max(hr_values) if hr_values else None,
            "resting": resting_value,
            "resting_is_real": resting_is_real,
            "samples": len(hr_values),
            "stdev": round(statistics.pstdev(hr_values), 1) if len(hr_values) > 1 else 0.0,
        })

    # 7-day rolling average of the daily average (skip days with no HR data)
    for i, s in enumerate(stats):
        window = [w for w in stats[max(0, i - 6):i + 1] if w["avg"] is not None]
        s["rolling_avg"] = round(statistics.mean(w["avg"] for w in window), 1) if window else None

    return stats


def scale(value, domain_min, domain_max, range_min, range_max):
    if domain_max == domain_min:
        return (range_min + range_max) / 2
    frac = (value - domain_min) / (domain_max - domain_min)
    return range_min + frac * (range_max - range_min)


def build_trend_chart(stats, chart_id="trendChart"):
    shown = [s for s in stats[-MAX_DAYS_SHOWN:] if s["avg"] is not None]
    if not shown:
        return "<p class='empty'>No data yet.</p>"

    W, H = 720, 300
    pad_l, pad_r, pad_t, pad_b = 46, 16, 16, 32
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b

    all_vals = [s["min"] for s in shown] + [s["max"] for s in shown]
    y_min = max(30, min(all_vals) - 5)
    y_max = min(200, max(all_vals) + 5)

    n = len(shown)

    def x_at(i):
        if n == 1:
            return pad_l + plot_w / 2
        return pad_l + (i / (n - 1)) * plot_w

    def y_at(v):
        return pad_t + plot_h - scale(v, y_min, y_max, 0, plot_h)

    top_pts = [(x_at(i), y_at(s["max"])) for i, s in enumerate(shown)]
    bot_pts = [(x_at(i), y_at(s["min"])) for i, s in enumerate(shown)]
    band_path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in top_pts)
    band_path += " L " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in reversed(bot_pts))
    band_path += " Z"

    avg_pts = [(x_at(i), y_at(s["avg"])) for i, s in enumerate(shown)]
    avg_path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in avg_pts)

    roll_shown = [(i, s) for i, s in enumerate(shown) if s["rolling_avg"] is not None]
    roll_path = ""
    if roll_shown:
        roll_pts = [(x_at(i), y_at(s["rolling_avg"])) for i, s in roll_shown]
        roll_path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in roll_pts)

    gridlines = []
    n_grid = 4
    for gi in range(n_grid + 1):
        v = y_min + (y_max - y_min) * gi / n_grid
        y = y_at(v)
        gridlines.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{W - pad_r}" y2="{y:.1f}" '
            f'class="gridline" />'
            f'<text x="{pad_l - 8}" y="{y + 4:.1f}" class="axis-label" '
            f'text-anchor="end">{round(v)}</text>'
        )

    x_labels = []
    label_idxs = sorted(set([0, n // 2, n - 1]))
    for i in label_idxs:
        d = shown[i]["date"]
        x_labels.append(
            f'<text x="{x_at(i):.1f}" y="{H - 8}" class="axis-label" '
            f'text-anchor="middle">{d.strftime("%b %d")}</text>'
        )

    hover_points = []
    for i, s in enumerate(shown):
        x = x_at(i)
        y = y_at(s["avg"])
        resting_label = f"{s['resting']} bpm" + ("" if s["resting_is_real"] else " (est.)")
        label = (
            f"{s['date'].strftime('%a %b %d')} — "
            f"avg {s['avg']} bpm, range {s['min']}-{s['max']}, "
            f"7d avg {s['rolling_avg']}, resting {resting_label}"
        )
        hover_points.append(
            f'<circle class="hoverpoint" cx="{x:.1f}" cy="{y:.1f}" r="10" '
            f'data-label="{label}"><title>{label}</title></circle>'
        )

    svg = f'''
<svg viewBox="0 0 {W} {H}" class="viz-root chart-svg" id="{chart_id}"
     role="img" aria-label="Daily heart rate trend, last {n} days">
  <rect x="0" y="0" width="{W}" height="{H}" fill="var(--surface-1)" />
  {"".join(gridlines)}
  <path d="{band_path}" class="band-fill" />
  <path d="{avg_path}" class="line-avg" fill="none" />
  {f'<path d="{roll_path}" class="line-rolling" fill="none" />' if roll_path else ''}
  {"".join(x_labels)}
  {"".join(hover_points)}
</svg>
'''
    return svg


def build_intraday_chart(rows, day, chart_id="intradayChart"):
    samples = [(ts, hr) for ts, hr, _rhr in rows if ts.date() == day and hr is not None]
    if not samples:
        return "<p class='empty'>No heart-rate samples for this day.</p>"

    W, H = 720, 220
    pad_l, pad_r, pad_t, pad_b = 46, 16, 16, 32
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b

    vals = [hr for _, hr in samples]
    y_min = max(30, min(vals) - 5)
    y_max = min(200, max(vals) + 5)

    day_start = datetime.combine(day, datetime.min.time())
    minute_max = 24 * 60

    def x_at(ts):
        minutes = (ts - day_start).total_seconds() / 60
        return pad_l + (minutes / minute_max) * plot_w

    def y_at(v):
        return pad_t + plot_h - scale(v, y_min, y_max, 0, plot_h)

    pts = [(x_at(ts), y_at(hr)) for ts, hr in samples]
    path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    gridlines = []
    n_grid = 4
    for gi in range(n_grid + 1):
        v = y_min + (y_max - y_min) * gi / n_grid
        y = y_at(v)
        gridlines.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{W - pad_r}" y2="{y:.1f}" '
            f'class="gridline" />'
            f'<text x="{pad_l - 8}" y="{y + 4:.1f}" class="axis-label" '
            f'text-anchor="end">{round(v)}</text>'
        )

    x_labels = []
    for hour in (0, 6, 12, 18, 24):
        minute = min(hour * 60, minute_max)
        x = pad_l + (minute / minute_max) * plot_w
        label = f"{hour:02d}:00" if hour < 24 else "24:00"
        x_labels.append(
            f'<text x="{x:.1f}" y="{H - 8}" class="axis-label" '
            f'text-anchor="middle">{label}</text>'
        )

    hover_points = []
    step = max(1, len(samples) // 60)
    for i in range(0, len(samples), step):
        ts, hr = samples[i]
        x, y = x_at(ts), y_at(hr)
        label = f"{ts.strftime('%H:%M')} — {hr} bpm"
        hover_points.append(
            f'<circle class="hoverpoint" cx="{x:.1f}" cy="{y:.1f}" r="9" '
            f'data-label="{label}"><title>{label}</title></circle>'
        )

    svg = f'''
<svg viewBox="0 0 {W} {H}" class="viz-root chart-svg" id="{chart_id}"
     role="img" aria-label="Heart rate through the day on {day.isoformat()}">
  <rect x="0" y="0" width="{W}" height="{H}" fill="var(--surface-1)" />
  {"".join(gridlines)}
  <path d="{path}" class="line-avg" fill="none" />
  {"".join(x_labels)}
  {"".join(hover_points)}
</svg>
'''
    return svg


def build_table(stats):
    rows_html = []
    for s in reversed(stats[-14:]):
        resting_cell = "—" if s["resting"] is None else (
            f"{s['resting']}" if s["resting_is_real"] else f"{s['resting']}~"
        )
        avg_cell = s["avg"] if s["avg"] is not None else "—"
        min_cell = s["min"] if s["min"] is not None else "—"
        max_cell = s["max"] if s["max"] is not None else "—"
        rows_html.append(
            f"<tr><td>{s['date'].strftime('%a %b %d')}</td>"
            f"<td>{avg_cell}</td><td>{min_cell}</td><td>{max_cell}</td>"
            f"<td>{resting_cell}</td><td>{s['stdev']}</td>"
            f"<td>{s['samples']}</td></tr>"
        )
    return "".join(rows_html)


def build_stat_tiles(stats):
    with_avg = [s for s in stats if s["avg"] is not None]
    if not with_avg:
        return "<p class='empty'>No data yet — run ingest.py after your first export lands in incoming/.</p>"

    latest = with_avg[-1]
    prior_week = with_avg[-8:-1] if len(with_avg) >= 8 else with_avg[:-1]

    def delta_str(current, baseline_list, key):
        vals = [s[key] for s in baseline_list if s[key] is not None]
        if not vals or current is None:
            return ""
        baseline = round(statistics.mean(vals), 1)
        diff = round(current - baseline, 1)
        if diff == 0:
            return "same as your 7-day average"
        direction = "higher" if diff > 0 else "lower"
        return f"{abs(diff)} bpm {direction} than your 7-day average"

    resting_delta = delta_str(latest["resting"], prior_week, "resting")
    avg_delta = delta_str(latest["avg"], prior_week, "avg")
    resting_note = "" if latest["resting_is_real"] else " (est.)"

    total_days = len(stats)
    total_samples = sum(s["samples"] for s in stats)

    tiles = [
        ("Latest resting HR" + resting_note, f"{latest['resting']} bpm", resting_delta),
        ("Latest daily average", f"{latest['avg']} bpm", avg_delta),
        ("Days tracked", str(total_days), ""),
        ("Total samples", f"{total_samples:,}", ""),
    ]

    html = []
    for label, value, sub in tiles:
        sub_html = f'<div class="tile-sub">{sub}</div>' if sub else ""
        html.append(
            f'<div class="tile"><div class="tile-label">{label}</div>'
            f'<div class="tile-value">{value}</div>{sub_html}</div>'
        )
    return "".join(html)


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Heart Rate Dashboard</title>
<style>
  :root {{ color-scheme: light; }}
  .viz-root {{
    --surface-1:      #fcfcfb;
    --text-primary:   #0b0b0b;
    --text-secondary: #52514e;
    --muted:          #898781;
    --gridline:       #e1e0d9;
    --baseline:       #c3c2b7;
    --series-1:       #2a78d6;
    --series-3:       #1baf7a;
    --band-fill:      rgba(42, 120, 214, 0.12);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) {{ color-scheme: dark; }}
    :root:where(:not([data-theme="light"])) .viz-root {{
      --surface-1:      #1a1a19;
      --text-primary:   #ffffff;
      --text-secondary: #c3c2b7;
      --muted:          #898781;
      --gridline:       #2c2c2a;
      --baseline:       #383835;
      --series-1:       #3987e5;
      --series-3:       #199e70;
      --band-fill:      rgba(57, 135, 229, 0.16);
    }}
  }}
  :root[data-theme="dark"] .viz-root {{
    --surface-1:      #1a1a19;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --muted:          #898781;
    --gridline:       #2c2c2a;
    --baseline:       #383835;
    --series-1:       #3987e5;
    --series-3:       #199e70;
    --band-fill:      rgba(57, 135, 229, 0.16);
  }}

  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    background: #f9f9f7;
    color: #0b0b0b;
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #0d0d0d; color: #ffffff; }}
  }}
  .wrap {{ max-width: 800px; margin: 0 auto; padding: 24px 16px 64px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  .subtitle {{ color: var(--text-secondary, #52514e); font-size: 13px; margin: 0 0 24px; }}

  .tiles {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 28px; }}
  @media (min-width: 560px) {{ .tiles {{ grid-template-columns: repeat(4, 1fr); }} }}
  .tile {{
    background: var(--surface-1, #fcfcfb);
    border: 1px solid rgba(11,11,11,0.10);
    border-radius: 10px;
    padding: 14px;
  }}
  @media (prefers-color-scheme: dark) {{
    .tile {{ border-color: rgba(255,255,255,0.10); }}
  }}
  .tile-label {{ font-size: 12px; color: #898781; margin-bottom: 6px; }}
  .tile-value {{ font-size: 22px; font-weight: 600; }}
  .tile-sub {{ font-size: 11px; color: #898781; margin-top: 4px; }}

  section {{ margin-bottom: 32px; }}
  h2 {{ font-size: 15px; margin: 0 0 4px; }}
  .section-note {{ font-size: 12px; color: #898781; margin: 0 0 10px; }}

  .chart-card {{
    background: var(--surface-1, #fcfcfb);
    border: 1px solid rgba(11,11,11,0.10);
    border-radius: 10px;
    padding: 12px;
    position: relative;
  }}
  @media (prefers-color-scheme: dark) {{
    .chart-card {{ border-color: rgba(255,255,255,0.10); }}
  }}
  .chart-svg {{ width: 100%; height: auto; display: block; }}
  .gridline {{ stroke: var(--gridline); stroke-width: 1; }}
  .axis-label {{ fill: var(--muted); font-size: 10px; }}
  .band-fill {{ fill: var(--band-fill); stroke: none; }}
  .line-avg {{ stroke: var(--series-1); stroke-width: 2; }}
  .line-rolling {{ stroke: var(--series-3); stroke-width: 2; stroke-dasharray: 5 3; }}
  .hoverpoint {{ fill: transparent; cursor: pointer; }}
  .hoverpoint:hover {{ fill: var(--series-1); opacity: 0.25; }}

  .legend {{ display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary, #52514e);
             margin: 8px 2px 0; flex-wrap: wrap; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .swatch {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
  .swatch.avg {{ background: #2a78d6; }}
  .swatch.rolling {{ background: #1baf7a; }}
  .swatch.band {{ background: rgba(42,120,214,0.25); }}

  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: right; padding: 6px 8px; }}
  th:first-child, td:first-child {{ text-align: left; }}
  th {{ color: #898781; font-weight: 500; border-bottom: 1px solid var(--gridline, #e1e0d9); }}
  tr:not(:last-child) td {{ border-bottom: 1px solid var(--gridline, #e1e0d9); }}

  .empty {{ color: #898781; font-size: 13px; }}
  footer {{ font-size: 11px; color: #898781; margin-top: 32px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Heart Rate Dashboard</h1>
  <p class="subtitle">Generated {generated_at} · Apple Watch data via Health Auto Export</p>

  <div class="tiles">
    {tiles_html}
  </div>

  <section>
    <h2>Daily trend (last {n_days} days)</h2>
    <p class="section-note">Shaded band = daily min–max range. Solid line = daily average. Dashed line = 7-day rolling average.</p>
    <div class="chart-card">
      {trend_chart}
    </div>
    <div class="legend">
      <span class="legend-item"><span class="swatch band"></span> Daily range</span>
      <span class="legend-item"><span class="swatch avg"></span> Daily average</span>
      <span class="legend-item"><span class="swatch rolling"></span> 7-day rolling average</span>
    </div>
  </section>

  <section>
    <h2>Most recent day — intraday</h2>
    <p class="section-note">{latest_day_label}</p>
    <div class="chart-card">
      {intraday_chart}
    </div>
    <div class="legend">
      <span class="legend-item"><span class="swatch avg"></span> Heart rate (bpm)</span>
    </div>
  </section>

  <section>
    <h2>Last 14 days — table view</h2>
    <p class="section-note">"Resting" uses Apple's own Resting Heart Rate reading when your export includes one for that day; a "~" marks days where none was available and an estimate (mean of the lowest ~10% of that day's samples) is shown instead.</p>
    <table>
      <thead>
        <tr><th>Date</th><th>Avg</th><th>Min</th><th>Max</th><th>Resting</th><th>Std dev</th><th>Samples</th></tr>
      </thead>
      <tbody>
        {table_rows}
      </tbody>
    </table>
  </section>

  <footer>
    MVP dashboard — sampling density depends on how often Apple Watch records HR in the background.
    Re-run <code>python3 scripts/update_dashboard.py</code> after each new export lands in <code>incoming/</code>.
  </footer>
</div>
</body>
</html>
"""


def main():
    rows = load_master()
    stats = compute_daily_stats(rows)

    tiles_html = build_stat_tiles(stats)
    trend_chart = build_trend_chart(stats)

    days_with_hr = [s["date"] for s in stats if s["avg"] is not None]
    if days_with_hr:
        latest_day = days_with_hr[-1]
        latest_day_label = latest_day.strftime("%A, %B %d, %Y")
        intraday_chart = build_intraday_chart(rows, latest_day)
    else:
        latest_day_label = "No data yet"
        intraday_chart = "<p class='empty'>No data yet.</p>"

    table_rows = build_table(stats) if stats else ""

    html = PAGE_TEMPLATE.format(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        tiles_html=tiles_html,
        n_days=min(len([s for s in stats if s["avg"] is not None]), MAX_DAYS_SHOWN),
        trend_chart=trend_chart,
        latest_day_label=latest_day_label,
        intraday_chart=intraday_chart,
        table_rows=table_rows,
    )

    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text(html)
    print(f"Dashboard written to {DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
