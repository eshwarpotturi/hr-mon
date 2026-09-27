#!/usr/bin/env python3
"""
ingest.py

Reads every CSV dropped in ../incoming/ (this is where Health Auto
Export's iCloud Drive automation saves daily exports), extracts Heart
Rate and Resting Heart Rate, merges into one running master dataset at
../data/heart_rate_master.csv (deduped by timestamp, sorted), and
archives processed files into ../incoming/processed/.

IMPORTANT column-detection note: this automation's export bundles many
metrics into ONE wide CSV per day (exportDataType "healthMetrics"),
and several column names all contain the substring "heart rate":
    "Walking Heart Rate Average (count/min)"
    "Resting Heart Rate (count/min)"
    "Heart Rate Variability (ms)"
    "Heart Rate (count/min)"          <- the one we actually want
A naive "contains 'heart rate'" match would grab the wrong column (the
first one in header order). This script instead strips the trailing
"(unit)" suffix and requires an EXACT match on the normalized metric
name, so "Walking Heart Rate Average" and "Heart Rate Variability"
are never confused with plain "Heart Rate".

Run:
    python3 ingest.py
"""
import csv
import re
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
INCOMING_DIR = BASE / "incoming"
PROCESSED_DIR = INCOMING_DIR / "processed"
DATA_DIR = BASE / "data"
MASTER_PATH = DATA_DIR / "heart_rate_master.csv"

# The real Health Auto Export files have one row per minute under
# "Date/Time", with "Heart Rate [Min]/[Max]/[Avg] (bpm)" columns. Heart rate
# is taken from the [Min] column only; [Max] and [Avg] are ignored.
DATE_EXACT_NAMES = ["date", "date/time", "startdate", "start date", "timestamp"]
HR_EXACT_NAMES = ["heart rate [min]"]
RESTING_HR_EXACT_NAMES = ["resting heart rate"]

# master csv column -> header names it can come from
FIELDS = {
    "heart_rate": HR_EXACT_NAMES,
    "resting_heart_rate": RESTING_HR_EXACT_NAMES,
}

DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S %z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%d-%b-%Y %I:%M:%S %p",
]

UNIT_SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")


def normalize_column(name: str) -> str:
    """'Heart Rate (count/min)' -> 'heart rate'
       'Walking Heart Rate Average (count/min)' -> 'walking heart rate average'
       'Resting Heart Rate (count/min)' -> 'resting heart rate'
    """
    stripped = UNIT_SUFFIX_RE.sub("", name).strip().lower()
    return stripped


def find_exact_column(header, exact_names):
    """Return the first original header whose normalized form exactly
    matches one of exact_names. This deliberately does NOT do substring
    matching, so 'Walking Heart Rate Average' never matches 'heart rate'."""
    normalized = [(h, normalize_column(h)) for h in header]
    for target in exact_names:
        for orig, norm in normalized:
            if norm == target:
                return orig
    return None


def parse_timestamp(raw: str):
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=None)
        except ValueError:
            continue
    return None


def read_master():
    """Returns dict {timestamp_str: {field: int|None for field in FIELDS}}"""
    records = {}
    if MASTER_PATH.exists():
        with MASTER_PATH.open(newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = row.get("timestamp")
                if not ts:
                    continue
                records[ts] = {field: safe_number(row.get(field)) for field in FIELDS}
    return records


def write_master(records: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with MASTER_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", *FIELDS])
        for ts in sorted(records.keys()):
            rec = records[ts]
            writer.writerow([ts] + [
                rec.get(field) if rec.get(field) is not None else "" for field in FIELDS
            ])


def safe_number(raw):
    if raw is None:
        return None
    raw = raw.strip()
    if raw == "":
        return None
    try:
        return int(round(float(raw)))
    except ValueError:
        return None


def process_file(path: Path, records: dict) -> tuple:
    added_hr = 0
    added_rhr = 0
    with path.open(newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return 0, 0

        date_col = find_exact_column(header, DATE_EXACT_NAMES)
        cols = {field: find_exact_column(header, names) for field, names in FIELDS.items()}

        if date_col is None:
            print(f"  skip {path.name}: no date/timestamp column found "
                  f"(header={header})")
            return 0, 0
        if cols["heart_rate"] is None and cols["resting_heart_rate"] is None:
            print(f"  skip {path.name}: no Heart Rate or Resting Heart Rate "
                  f"column found (header={header})")
            return 0, 0

        date_idx = header.index(date_col)
        idxs = {field: header.index(col) for field, col in cols.items() if col}

        found = ", ".join(f'{field}="{col}"' for field, col in cols.items() if col)
        print(f"  {path.name}: date='{date_col}', {found}")

        for row in reader:
            if len(row) <= date_idx:
                continue
            ts = parse_timestamp(row[date_idx])
            if ts is None:
                continue

            values = {
                field: safe_number(row[i]) if len(row) > i else None
                for field, i in idxs.items()
            }
            if values.get("heart_rate") is None and values.get("resting_heart_rate") is None:
                continue  # nothing useful on this row

            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            existing = records.get(ts_str, dict.fromkeys(FIELDS))
            if values.get("heart_rate") is not None and existing.get("heart_rate") is None:
                added_hr += 1
            if values.get("resting_heart_rate") is not None and existing.get("resting_heart_rate") is None:
                added_rhr += 1

            for field, value in values.items():
                if value is not None:
                    existing[field] = value
            records[ts_str] = existing

    return added_hr, added_rhr


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
    total_hr, total_rhr = 0, 0

    for path in csv_files:
        added_hr, added_rhr = process_file(path, records)
        total_hr += added_hr
        total_rhr += added_rhr
        shutil.move(str(path), str(PROCESSED_DIR / path.name))

    write_master(records)
    print(
        f"\nDone. +{total_hr} heart-rate samples, +{total_rhr} resting-HR "
        f"readings ({starting_count} -> {len(records)} total timestamps). "
        f"Master dataset: {MASTER_PATH}"
    )


if __name__ == "__main__":
    main()
