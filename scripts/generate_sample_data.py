#!/usr/bin/env python3
"""
generate_sample_data.py

Creates synthetic daily heart-rate CSVs in the same shape that the
"Health Auto Export" iOS app produces, so we can build and test the
ingestion + dashboard pipeline before real Apple Watch data is flowing in.

Format matches Health Auto Export's per-metric CSV export:
    Date,Heart Rate (count/min)
    2026-09-20 00:03:11,61
    2026-09-20 00:11:47,58
    ...

Run:
    python3 generate_sample_data.py
Writes one CSV per day into ../incoming/
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


def hr_for_minute(minute_of_day: int, day_offset: int) -> int:
    """Simulate a plausible daily heart-rate curve with noise.

    - Deep sleep (0:00-6:00): low, ~48-55 bpm
    - Waking / morning (6:00-9:00): rising, some spikes (getting up, commute)
    - Work hours (9:00-18:00): resting baseline ~65-75, occasional stress spikes
    - Evening (18:00-22:00): moderate, maybe one exercise spike
    - Late night (22:00-24:00): winding down
    Adds a slow day-to-day drift so the trend isn't perfectly flat.
    """
    hour = minute_of_day / 60.0
    drift = math.sin(day_offset / 3.5) * 2.5  # slow multi-day wobble

    if 0 <= hour < 6:
        base = 50 + 4 * math.sin(hour)
    elif 6 <= hour < 9:
        base = 55 + (hour - 6) * 6
    elif 9 <= hour < 18:
        base = 70 + 3 * math.sin((hour - 9) * 1.3)
        # random workday stress spikes
        if random.random() < 0.01:
            base += random.uniform(15, 35)
    elif 18 <= hour < 20:
        base = 72
        # occasional evening workout window
        if 18.5 <= hour <= 19.25 and day_offset % 3 == 0:
            base += 45 + 10 * math.sin((hour - 18.5) * 8)
    elif 20 <= hour < 22:
        base = 68 - (hour - 20) * 3
    else:
        base = 58 - (hour - 22) * 2

    noise = random.gauss(0, 2.2)
    value = base + drift + noise
    return max(40, min(180, round(value)))


def main():
    today = date.today()
    start_day = today - timedelta(days=NUM_DAYS - 1)

    for day_offset in range(NUM_DAYS):
        day = start_day + timedelta(days=day_offset)
        rows = []

        # Simulate Apple Watch's real sampling behavior for the MVP:
        # denser during movement/waking hours, sparser overnight.
        minute = 0
        while minute < 24 * 60:
            hour = minute / 60.0
            if 0 <= hour < 6:
                step = random.choice([8, 10, 12])   # sparse overnight
            elif 9 <= hour < 18:
                step = random.choice([3, 5, 6])      # denser during day
            else:
                step = random.choice([5, 7, 8])
            ts = datetime.combine(day, datetime.min.time()) + timedelta(minutes=minute)
            hr = hr_for_minute(minute, day_offset)
            rows.append((ts.strftime("%Y-%m-%d %H:%M:%S"), hr))
            minute += step

        out_path = INCOMING_DIR / f"HeartRate_{day.isoformat()}.csv"
        with out_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Heart Rate (count/min)"])
            writer.writerows(rows)
        print(f"wrote {out_path.name}  ({len(rows)} samples)")


if __name__ == "__main__":
    main()
