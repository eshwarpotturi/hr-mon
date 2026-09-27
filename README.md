# Heart Rate Monitor

Apple Watch → Health app → Health Auto Export (iPhone) → iCloud Drive → this
Mac → trend dashboard + daily reports, pushed to this (private) repo.

## How data gets here

Health Auto Export's automation (`automationExportBaseName: "Hr"`) writes one
wide CSV per day, one row per minute, to its own iCloud container, which this
Mac sees at:

```
~/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/Daily hr/
    Hr-HealthMetrics-YYYY-MM-DD.csv
```

The app needs to be opened on the iPhone for the export to run (iOS blocks
background Health access while the phone is locked), so treat its 9pm
reminder as your cue.

**Columns used**: the file has ~19 metrics. `ingest.py` takes heart rate from
**`Heart Rate [Min] (bpm)` only** (not `[Max]` or `[Avg]`), plus Apple's
once-a-day `Resting Heart Rate (bpm)`. Columns are matched by exact name after
stripping the unit, so look-alikes such as `Walking Heart Rate Average` or
`Heart Rate Variability` are never picked up.

## Daily automation (8:00 AM)

A launchd job runs `scripts/daily.py` every day at 8:00 AM (or when the Mac
wakes, if it was asleep). It:

1. Looks for new entries in the iCloud folder above: a file with no copy in
   `incoming/processed/`, or whose contents changed since it was last read.
2. If there are none, logs "No new entry" and stops.
3. Otherwise copies them into `incoming/`, runs `update_dashboard.py`
   (ingest → dashboard → reports), then commits `reports/`, `data/`,
   `dashboard/` and `incoming/processed/` as "Daily update YYYY-MM-DD" and
   pushes to GitHub. If the push fails, the commit stays local and goes out
   with the next successful push.

Output goes to `logs/daily.log` (not committed).

```bash
# run it now, exactly as the 8 AM trigger would
launchctl kickstart gui/$(id -u)/com.hrmon.daily

# see whether it's loaded and how the last run exited
launchctl print gui/$(id -u)/com.hrmon.daily | grep -E "state|last exit"

# install (the job definition lives in launchd/)
cp launchd/com.hrmon.daily.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hrmon.daily.plist

# remove
launchctl bootout gui/$(id -u)/com.hrmon.daily
rm ~/Library/LaunchAgents/com.hrmon.daily.plist
```

If the log shows `Operation not permitted` / `Can't read the export folder`,
give `/opt/anaconda3/bin/python3.12` Full Disk Access in System Settings →
Privacy & Security.

## Running by hand

```bash
python3 scripts/daily.py            # same as the scheduled job
python3 scripts/update_dashboard.py # just process whatever is in incoming/
open dashboard/index.html
```

## Folder layout

```
hr-mon/
├── incoming/          <- new exports are copied here
│   └── processed/     <- ingest.py archives files here once merged
├── data/
│   └── heart_rate_master.csv   <- running, deduped dataset: timestamp, heart_rate, resting_heart_rate
├── dashboard/
│   └── index.html     <- open in a browser; regenerated each run
├── reports/
│   ├── daily_stats.csv    <- one row per day (avg/min/max/resting/stdev/samples/7-day avg)
│   └── YYYY-MM-DD.md      <- one summary per day
├── scripts/
│   ├── daily.py              <- the 8 AM job: check iCloud, update, commit, push
│   ├── ingest.py             <- merges incoming/*.csv into data/heart_rate_master.csv
│   ├── build_dashboard.py    <- reads the master csv, writes dashboard/index.html
│   ├── report.py             <- reads the master csv, writes reports/
│   ├── update_dashboard.py   <- runs ingest, build_dashboard, report in order
│   └── generate_sample_data.py  <- fake data in the old single-column format (no longer ingested)
├── launchd/
│   └── com.hrmon.daily.plist <- the 8 AM job definition
└── logs/daily.log     <- job output (gitignored)
```

## Notes

- **Sampling density**: Apple Watch records HR in the background roughly
  every 5–10 minutes at rest, more often when moving — plenty for daily
  trends.
- **Resting HR**: Apple's own reading when the day's export has one; otherwise
  an estimate (mean of the lowest ~10% of that day's samples), marked `~` in
  the dashboard table and "estimate" in the reports.
- A day with no heart-rate samples yet (e.g. today's partial export) is left
  out until data arrives; the next run picks up the updated file.
