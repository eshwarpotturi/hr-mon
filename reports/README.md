# Heart rate report

**Data from 21 Sep 2026 to 29 Sep 2026, 16:12** · 8 days · 979 readings · heart rate from the `Heart Rate [Min] (bpm)` column.

## Latest day: Tuesday 29 September

| | This day | Your usual (average of previous days) | Compared with usual |
|---|---|---|---|
| Average HR | 90.5 | 88.3 | ▲ 2.2 higher |
| Resting HR | 63 | 73 | ▼ 10 lower |
| Lowest reading | 52 | 49.7 | ▲ 2.3 higher |
| Highest reading | 132 | 128.3 | ▲ 3.7 higher |
| Variability (std dev) | 19.7 | 17.4 | ▲ 2.3 higher |

Resting HR for this day is Apple's own resting reading. 83 readings. [Full day report](2026-09-29.md)

![Every reading on Tue 29 Sep](latest_day.svg)

## This week vs last week

| | This week (Tue 22 Sep – Tue 29 Sep) | Previous week | Change |
|---|---|---|---|
| Average HR | 87.9 | 93.1 | ▼ 5.2 lower |
| Resting HR | 71.7 | 72 | ▼ 0.3 lower |
| Lowest reading | 44 | 50 | ▼ 6 lower |
| Highest reading | 160 | 132 | ▲ 28 higher |
| Variability (std dev) | 17.3 | 20.2 | ▼ 2.9 lower |

_Previous week has 1 of 7 days so far; the comparison is complete after 6 more day(s) of data._

## Trends

**Every reading**: each dot is one heart-rate sample at its real time; gaps are when the watch wasn't recording. The orange line is Apple's resting HR for that day.

![Every heart-rate reading](all_readings.svg)

**Daily average** (bars) and **7-day rolling average** (line).

```mermaid
xychart-beta
    title "Daily average heart rate"
    x-axis ["21 Sep", "22 Sep", "23 Sep", "24 Sep", "25 Sep", "26 Sep", "28 Sep", "29 Sep"]
    y-axis "bpm" 70 --> 110
    bar [93.1, 97.7, 85.1, 83.4, 84.8, 83.1, 90.9, 90.5]
    line [93.1, 95.4, 92.0, 89.8, 88.8, 87.9, 88.3, 87.9]
```

**Daily range**: highest reading (top line), average (middle), lowest reading (bottom).

```mermaid
xychart-beta
    title "Daily range"
    x-axis ["21 Sep", "22 Sep", "23 Sep", "24 Sep", "25 Sep", "26 Sep", "28 Sep", "29 Sep"]
    y-axis "bpm" 30 --> 180
    line [132, 160, 120, 125, 108, 129, 124, 132]
    line [93.1, 97.7, 85.1, 83.4, 84.8, 83.1, 90.9, 90.5]
    line [50, 52, 50, 44, 51, 52, 49, 52]
```

**Resting heart rate.** A lower resting HR over time usually goes with better fitness and recovery; short spikes often follow poor sleep, stress, illness or alcohol.

```mermaid
xychart-beta
    title "Resting heart rate"
    x-axis ["21 Sep", "22 Sep", "23 Sep", "24 Sep", "25 Sep", "26 Sep", "28 Sep", "29 Sep"]
    y-axis "bpm" 50 --> 100
    line [72, 83, 72, 70, 81, 65, 68, 63]
```

## Highlights

| | Day | Value |
|---|---|---|
| Lowest resting HR | [Tue 29 Sep](2026-09-29.md) | 63 bpm |
| Highest resting HR | [Tue 22 Sep](2026-09-22.md) | 83 bpm |
| Calmest day (lowest average) | [Sat 26 Sep](2026-09-26.md) | 83.1 bpm |
| Busiest day (highest average) | [Tue 22 Sep](2026-09-22.md) | 97.7 bpm |
| Highest single reading | [Tue 22 Sep](2026-09-22.md) | 160 bpm |
| Most variable day | [Tue 22 Sep](2026-09-22.md) | 22.7 |

## Every day

Compared with your overall average of **88.6 bpm** (resting **71.8 bpm**). Newest first.

| Day | Avg | vs overall | Resting | vs overall | Min | Max | Std dev | Readings |
|---|---|---|---|---|---|---|---|---|
| [Tue 29 Sep](2026-09-29.md) | 90.5 | ▲ 1.9 higher | 63 | ▼ 8.8 lower | 52 | 132 | 19.7 | 83 |
| [Mon 28 Sep](2026-09-28.md) | 90.9 | ▲ 2.3 higher | 68 | ▼ 3.8 lower | 49 | 124 | 20.4 | 152 |
| [Sat 26 Sep](2026-09-26.md) | 83.1 | ▼ 5.5 lower | 65 | ▼ 6.8 lower | 52 | 129 | 13.5 | 124 |
| [Fri 25 Sep](2026-09-25.md) | 84.8 | ▼ 3.8 lower | 81 | ▲ 9.2 higher | 51 | 108 | 13.5 | 68 |
| [Thu 24 Sep](2026-09-24.md) | 83.4 | ▼ 5.2 lower | 70 | ▼ 1.8 lower | 44 | 125 | 13.3 | 154 |
| [Wed 23 Sep](2026-09-23.md) | 85.1 | ▼ 3.5 lower | 72 | ▲ 0.2 higher | 50 | 120 | 17.9 | 101 |
| [Tue 22 Sep](2026-09-22.md) | 97.7 | ▲ 9.1 higher | 83 | ▲ 11.2 higher | 52 | 160 | 22.7 | 182 |
| [Mon 21 Sep](2026-09-21.md) | 93.1 | ▲ 4.5 higher | 72 | ▲ 0.2 higher | 50 | 132 | 20.2 | 115 |

`~` = resting HR estimated (no Apple reading that day). 

<details><summary>What the numbers mean</summary>

- **Average HR**: mean of all readings that day.
- **Resting HR**: Apple's once-a-day resting value; if missing, the mean of that day's lowest 10% of readings.
- **Lowest / highest reading**: extremes across the day's readings.
- **Variability (std dev)**: how much HR moved around during the day; higher usually means more activity.
- **7-day rolling average**: average of the last 7 days' averages; smooths out single-day noise.
- **Readings**: Apple Watch samples HR every few minutes at rest, more often when active, so more readings usually means more wear time or activity.

Not medical advice.

</details>

Raw numbers: [daily_stats.csv](daily_stats.csv)
