#!/usr/bin/env python3
"""One command to run daily: ingest new CSVs, rebuild the dashboard, write reports/."""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def run(script_name):
    result = subprocess.run([sys.executable, str(SCRIPTS_DIR / script_name)])
    if result.returncode != 0:
        print(f"{script_name} failed (exit {result.returncode})")
        sys.exit(result.returncode)


def main():
    print("== ingest ==")
    run("ingest.py")
    print("\n== build dashboard ==")
    run("build_dashboard.py")
    print("\n== reports ==")
    run("report.py")
    print("\nDone. Open dashboard/index.html in your browser.")


if __name__ == "__main__":
    main()
