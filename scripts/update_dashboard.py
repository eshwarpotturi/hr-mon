#!/usr/bin/env python3
"""
update_dashboard.py

One command to run daily: ingest any new CSVs from incoming/, then
rebuild the dashboard. This is the script you'll eventually put on a
schedule (cron / launchd) once the MVP is working.

Run:
    python3 scripts/update_dashboard.py
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def run(script_name):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script_name)],
        capture_output=False,
    )
    if result.returncode != 0:
        print(f"{script_name} failed (exit {result.returncode})")
        sys.exit(result.returncode)


def main():
    print("== ingest ==")
    run("ingest.py")
    print("\n== build dashboard ==")
    run("build_dashboard.py")
    print("\nDone. Open dashboard/index.html in your browser.")


if __name__ == "__main__":
    main()
