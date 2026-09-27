# Heart rate report

**Data from 21 Sep 2026 to 26 Sep 2026, 22:56** · 6 days · 744 readings · heart rate from the `Heart Rate [Min] (bpm)` column.

## Latest day: Saturday 26 September

| | This day | Your usual (average of previous days) | Compared with usual |
|---|---|---|---|
| Average HR | 83.1 | 88.8 | ▼ 5.7 lower |
| Resting HR | 65 | 75.6 | ▼ 10.6 lower |
| Lowest reading | 52 | 49.4 | ▲ 2.6 higher |
| Highest reading | 129 | 129 | same |
| Variability (std dev) | 13.5 | 17.5 | ▼ 4.0 lower |

Resting HR for this day is Apple's own resting reading. 124 readings. [Full day report](2026-09-26.md)

```mermaid
xychart-beta
    title "Sat 26 Sep: average HR by hour"
    x-axis ["00h", "13h", "14h", "15h", "16h", "17h", "18h", "19h", "20h", "21h", "22h"]
    y-axis "bpm" 50 --> 110
    bar [66, 86.9, 76.4, 95, 85.8, 76.7, 79.9, 76.1, 84.8, 85.9, 75.7]
```

## This week vs last week

| | This week (Mon 21 Sep – Sat 26 Sep) | Previous week | Change |
|---|---|---|---|
| Average HR | 87.9 | — | — |
| Resting HR | 73.8 | — | — |
| Lowest reading | 44 | — | — |
| Highest reading | 160 | — | — |
| Variability (std dev) | 16.9 | — | — |

_Previous week has 0 of 7 days so far; the comparison is complete after 8 more day(s) of data._

## Trends

**Daily average** (bars) and **7-day rolling average** (line).

```mermaid
xychart-beta
    title "Daily average heart rate"
    x-axis ["21 Sep", "22 Sep", "23 Sep", "24 Sep", "25 Sep", "26 Sep"]
    y-axis "bpm" 70 --> 110
    bar [93.1, 97.7, 85.1, 83.4, 84.8, 83.1]
    line [93.1, 95.4, 92.0, 89.8, 88.8, 87.9]
```

**Daily range**: highest reading (top line), average (middle), lowest reading (bottom).

```mermaid
xychart-beta
    title "Daily range"
    x-axis ["21 Sep", "22 Sep", "23 Sep", "24 Sep", "25 Sep", "26 Sep"]
    y-axis "bpm" 30 --> 180
    line [132, 160, 120, 125, 108, 129]
    line [93.1, 97.7, 85.1, 83.4, 84.8, 83.1]
    line [50, 52, 50, 44, 51, 52]
```

**Resting heart rate.** A lower resting HR over time usually goes with better fitness and recovery; short spikes often follow poor sleep, stress, illness or alcohol.

```mermaid
xychart-beta
    title "Resting heart rate"
    x-axis ["21 Sep", "22 Sep", "23 Sep", "24 Sep", "25 Sep", "26 Sep"]
    y-axis "bpm" 50 --> 100
    line [72, 83, 72, 70, 81, 65]
```

## Highlights

| | Day | Value |
|---|---|---|
| Lowest resting HR | [Sat 26 Sep](2026-09-26.md) | 65 bpm |
| Highest resting HR | [Tue 22 Sep](2026-09-22.md) | 83 bpm |
| Calmest day (lowest average) | [Sat 26 Sep](2026-09-26.md) | 83.1 bpm |
| Busiest day (highest average) | [Tue 22 Sep](2026-09-22.md) | 97.7 bpm |
| Highest single reading | [Tue 22 Sep](2026-09-22.md) | 160 bpm |
| Most variable day | [Tue 22 Sep](2026-09-22.md) | 22.7 |

## Every day

Compared with your overall average of **87.9 bpm** (resting **73.8 bpm**). Newest first.

| Day | Avg | vs overall | Resting | vs overall | Min | Max | Std dev | Readings |
|---|---|---|---|---|---|---|---|---|
| [Sat 26 Sep](2026-09-26.md) | 83.1 | ▼ 4.8 lower | 65 | ▼ 8.8 lower | 52 | 129 | 13.5 | 124 |
| [Fri 25 Sep](2026-09-25.md) | 84.8 | ▼ 3.1 lower | 81 | ▲ 7.2 higher | 51 | 108 | 13.5 | 68 |
| [Thu 24 Sep](2026-09-24.md) | 83.4 | ▼ 4.5 lower | 70 | ▼ 3.8 lower | 44 | 125 | 13.3 | 154 |
| [Wed 23 Sep](2026-09-23.md) | 85.1 | ▼ 2.8 lower | 72 | ▼ 1.8 lower | 50 | 120 | 17.9 | 101 |
| [Tue 22 Sep](2026-09-22.md) | 97.7 | ▲ 9.8 higher | 83 | ▲ 9.2 higher | 52 | 160 | 22.7 | 182 |
| [Mon 21 Sep](2026-09-21.md) | 93.1 | ▲ 5.2 higher | 72 | ▼ 1.8 lower | 50 | 132 | 20.2 | 115 |

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
