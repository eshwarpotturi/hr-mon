#!/usr/bin/env python3
"""
daily.py

Run by launchd every day at 8:00 AM (see launchd/com.hrmon.daily.plist).

1. Looks in Health Auto Export's iCloud Drive folder for new entries: a
   Hr-HealthMetrics-*.csv with no copy in incoming/processed/, or whose
   contents changed (today's file keeps growing through the day).
2. If there are none, logs that and exits without touching anything.
3. Otherwise copies them into incoming/, runs update_dashboard.py
   (ingest -> dashboard -> reports), then commits reports/, data/,
   dashboard/ and incoming/processed/ and pushes to GitHub.

A failed push leaves the commit local; the next run's push includes it.

Run by hand:
    python3 scripts/daily.py
"""
import filecmp
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BASE = SCRIPTS_DIR.parent
INCOMING_DIR = BASE / "incoming"
PROCESSED_DIR = INCOMING_DIR / "processed"

EXPORT_DIR = (
    Path.home() / "Library" / "Mobile Documents"
    / "iCloud~com~ifunography~HealthExport" / "Documents" / "Daily hr"
)
EXPORT_GLOB = "Hr-HealthMetrics-*.csv"

GIT = "/usr/bin/git"
COMMIT_PATHS = ["reports", "data", "dashboard", "incoming/processed"]
COMMIT_TRAILER = (
    "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
    "\nClaude-Session: https://claude.ai/code/session_019fA9BGdpKoVFS9s4igMns6"
)


def is_new(src: Path) -> bool:
    for folder in (INCOMING_DIR, PROCESSED_DIR):
        existing = folder / src.name
        if existing.exists() and filecmp.cmp(src, existing, shallow=False):
            return False
    return True


def copy_new_exports() -> list:
    # iCloud may keep files cloud-only ("Optimize Mac Storage"); fetch first.
    subprocess.run(["brctl", "download", str(EXPORT_DIR)], capture_output=True)
    new_files = [src for src in sorted(EXPORT_DIR.glob(EXPORT_GLOB)) if is_new(src)]
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    for src in new_files:
        shutil.copy2(src, INCOMING_DIR / src.name)
        print(f"  new: {src.name}")
    return new_files


def git(*args) -> subprocess.CompletedProcess:
    return subprocess.run([GIT, *args], cwd=BASE, capture_output=True, text=True)


def commit_and_push(today: str) -> bool:
    git("add", "--", *COMMIT_PATHS)
    if git("diff", "--cached", "--quiet").returncode != 0:
        result = git("commit", "-m", f"Daily update {today}{COMMIT_TRAILER}")
        if result.returncode != 0:
            print(f"git commit failed:\n{result.stdout}{result.stderr}")
            return False
        print(f"Committed: Daily update {today}")
    else:
        print("No changes to commit.")
    result = git("push")
    if result.returncode != 0:
        print(f"git push failed (commit kept locally):\n{result.stderr}")
        return False
    print("Pushed to GitHub.")
    return True


def main():
    now = datetime.now()
    print(f"==== {now:%Y-%m-%d %H:%M:%S} ====")

    try:
        if not EXPORT_DIR.is_dir():
            print(f"Export folder not found: {EXPORT_DIR}")
            print("Is iCloud Drive on, and is Health Auto Export still saving there?")
            sys.exit(1)
        new_files = copy_new_exports()
    except PermissionError as e:
        print(f"Can't read the export folder: {e}")
        print("Grant Full Disk Access to this Python in System Settings "
              "> Privacy & Security.")
        sys.exit(1)

    if not new_files:
        print("No new entry. Nothing to do.\n")
        return

    result = subprocess.run([sys.executable, str(SCRIPTS_DIR / "update_dashboard.py")])
    if result.returncode != 0:
        print("update_dashboard.py failed; not committing.\n")
        sys.exit(result.returncode)

    ok = commit_and_push(f"{now:%Y-%m-%d}")
    print()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
