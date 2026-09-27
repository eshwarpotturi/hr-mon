#!/usr/bin/env python3
"""
ingest.py

Reads every CSV dropped in ../incoming/ (this is where the "Health Auto
Export" iOS app should save daily heart-rate exports, e.g. via iCloud
Drive), normalizes them, merges into one running master dataset at
../data/heart_rate_master.csv (deduped by timestamp, sorted), and archives
processed files into ../incoming/processed/ so they don't get re-read.

Column detection is flexible: it looks for a date/timestamp column and a
heart-rate column by name, so it tolerates the exact header Health Auto
Export uses (which has varied across its versions), e.g.:
    "Date", "Heart Rate (count/min)"
    "date", "Heart Rate (bpm)"
    "startDate", "value"

Run:
    python3 ingest.py
"""
import csv
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
INCOMING_DIR = BASE / "incoming"
PROCESSED_DIR = INCOMING_DIR / "processed"
DATA_DIR = BASE / "data"
MASTER_PATH = DATA_DIR / "heart_rate_master.csv"

DATE_COL_CANDIDATES = ["date", "startdate", "timestamp", "start_date"]
HR_COL_CANDIDATES = [
    "heart rate (count/min)",
    "heart rate (bpm)",
    "heart rate",
    "value",
    "hr",
]

DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S %z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%d-%b-%Y %I:%M:%S %p",
]


def parse_timestamp(raw: str):
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=None)  # normalize to naive local time
        except ValueError:
            continue
    return None


def find_column(header, candidates):
    lowered = {h.strip().lower(): h for h in header}
    for cand in candidates:
        if cand in lowered:
            return lowered[cand]
    # fallback: substring match
    for h_lower, h_orig in lowered.items():
        for cand in candidates:
            if cand in h_lower:
                return h_orig
    return None


def read_master():
    """Returns dict {timestamp_str: hr_int}"""
    records = {}
    if MASTER_PATH.exists():
        with MASTER_PATH.open(newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    records[row["timestamp"]] = int(round(float(row["heart_rate"])))
                except (ValueError, KeyError):
                    continue
    return records


def write_master(records: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with MASTER_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "heart_rate"])
        for ts in sorted(records.keys()):
            writer.writerow([ts, records[ts]])


def process_file(path: Path, records: dict) -> int:
    added = 0
    with path.open(newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return 0
        date_col = find_column(header, DATE_COL_CANDIDATES)
        hr_col = find_column(header, HR_COL_CANDIDATES)
        if date_col is None or hr_col is None:
            print(f"  skip {path.name}: could not detect date/HR columns "
                  f"(header={header})")
            return 0
        date_idx = header.index(date_col)
        hr_idx = header.index(hr_col)

        for row in reader:
            if len(row) <= max(date_idx, hr_idx):
                continue
            ts = parse_timestamp(row[date_idx])
            if ts is None:
                continue
            try:
                hr = int(round(float(row[hr_idx])))
            except ValueError:
                continue
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            if ts_str not in records:
                added += 1
            records[ts_str] = hr
    return added


def main():
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(
        p for p in INCOMING_DIR.glob("*.csv") if p.parent == INCOMING_DIR
    )
    if not csv_files:
        print("No new CSVs found in incoming/.")
        return

    records = read_master()
    starting_count = len(records)
    total_added = 0

    for path in csv_files:
        added = process_file(path, records)
        total_added += added
        print(f"  {path.name}: +{added} new samples")
        shutil.move(str(path), str(PROCESSED_DIR / path.name))

    write_master(records)
    print(
        f"\nDone. {total_added} new samples added "
        f"({starting_count} -> {len(records)} total). "
        f"Master dataset: {MASTER_PATH}"
    )


if __name__ == "__main__":
    main()
