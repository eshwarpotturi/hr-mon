#!/usr/bin/env python3
"""
generate_sample_data.py

Creates synthetic daily CSVs matching Eswar's actual Health Auto Export
automation config (id 3343BE10-...): exportDataType "healthMetrics" with
aggregateData=true, exportAggregation="Minutes", exportFileLength="day" —
i.e. ONE WIDE CSV PER DAY with a column per requested metric, aligned by
minute-level timestamp. Critically, several of those columns contain the
substring "heart rate":
    Walking Heart Rate Average, Resting Heart Rate, Heart Rate Variability,
    Heart Rate
This generator reproduces that exact column layout (same order as the
automation's "metrics" list) so the ingestion script's column-detection
logic gets genuinely tested against the real trap, not a simplified one.

Run:
    python3 generate_sample_data.py
Writes one CSV per day into ../incoming/ named Hr-YYYY-MM-DD.csv
(matching automationExportBaseName "Hr").
"""
import csv
import random
import math
from datetime import datetime, timedelta, date
from pathlib import Path

INCOMING_DIR = Path(__file__).resolve().parent.parent / "incoming"
INCOMING_DIR.mkdir(parents=True, exist_ok=True)

NUM_DAYS = 14
random.seed(42)

# Column order mirrors the automation's "metrics" list exactly, so the
# ingestion script has to correctly skip past every heart-rate-like decoy.
METRIC_COLUMNS = [
    "Walking Step Length (cm)",
    "Walking Speed (km/hr)",
    "Walking Heart Rate Average (count/min)",
    "Walking + Running Distance (km)",
    "Time in Daylight (min)",
    "Step Count (count)",
    "Resting Heart Rate (count/min)",
    "Respiratory Rate (count/min)",
    "Physical Effort (kcal/hr·kg)",
    "Heart Rate Variability (ms)",
    "Heart Rate (count/min)",
    "Blood Pressure (mmHg)",
    "Apple Stand Time (min)",
    "Apple Move Time (min)",
    "Apple Exercise Time (min)",
]


def hr_for_minute(minute_of_day: int, day_offset: int) -> float:
    hour = minute_of_day / 60.0
    drift = math.sin(day_offset / 3.5) * 2.5

    if 0 <= hour < 6:
        base = 50 + 4 * math.sin(hour)
    elif 6 <= hour < 9:
        base = 55 + (hour - 6) * 6
    elif 9 <= hour < 18:
        base = 70 + 3 * math.sin((hour - 9) * 1.3)
        if random.random() < 0.01:
            base += random.uniform(15, 35)
    elif 18 <= hour < 20:
        base = 72
        if 18.5 <= hour <= 19.25 and day_offset % 3 == 0:
            base += 45 + 10 * math.sin((hour - 18.5) * 8)
    elif 20 <= hour < 22:
        base = 68 - (hour - 20) * 3
    else:
        base = 58 - (hour - 22) * 2

    noise = random.gauss(0, 2.2)
    return max(40, min(180, round(base + drift + noise)))


def walking_hr_for_minute(hr):
    """Decoy metric — deliberately close in value to plain HR so a
    column-detection bug would go unnoticed without exact-name matching."""
    return round(hr + random.uniform(3, 10))


def main():
    today = date.today()
    start_day = today - timedelta(days=NUM_DAYS - 1)

    for day_offset in range(NUM_DAYS):
        day = start_day + timedelta(days=day_offset)
        rows = []

        # Apple's real Resting Heart Rate is a single daily value Apple
        # itself computes — appears once per day in the export, typically
        # on an early-morning row. We simulate that placement.
        resting_value = round(48 + drift_for_day(day_offset) + random.uniform(-2, 2), 0)

        minute = 0
        first_row_of_day = True
        while minute < 24 * 60:
            hour = minute / 60.0
            if 0 <= hour < 6:
                step = random.choice([8, 10, 12])
            elif 9 <= hour < 18:
                step = random.choice([3, 5, 6])
            else:
                step = random.choice([5, 7, 8])

            ts = datetime.combine(day, datetime.min.time()) + timedelta(minutes=minute)
            hr = hr_for_minute(minute, day_offset)

            row = {col: "" for col in METRIC_COLUMNS}
            row["Heart Rate (count/min)"] = hr
            row["Walking Heart Rate Average (count/min)"] = (
                walking_hr_for_minute(hr) if 6 <= hour < 20 and random.random() < 0.3 else ""
            )
            if first_row_of_day:
                row["Resting Heart Rate (count/min)"] = int(resting_value)
                first_row_of_day = False

            rows.append((ts.strftime("%Y-%m-%d %H:%M:%S"), row))
            minute += step

        out_path = INCOMING_DIR / f"Hr-{day.isoformat()}.csv"
        with out_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date"] + METRIC_COLUMNS)
            for ts_str, row in rows:
                writer.writerow([ts_str] + [row[c] for c in METRIC_COLUMNS])
        print(f"wrote {out_path.name}  ({len(rows)} rows, {len(METRIC_COLUMNS)+1} columns)")


def drift_for_day(day_offset):
    return math.sin(day_offset / 4.0) * 1.5


if __name__ == "__main__":
    main()
