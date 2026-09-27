# Heart Rate Monitor

Apple Watch → Health app → Health Auto Export (iPhone) → iPhone Shortcut
uploads the CSV to this (private) repo → GitHub Actions builds the trend
dashboard + daily reports.

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

## Automation: iPhone → GitHub (no Mac needed)

1. **iPhone Shortcut** (`shortcut/Upload HR to GitHub.shortcut`) uploads the
   newest file in `Daily hr` to `incoming/` in this repo through the GitHub
   API. A Shortcuts automation runs it when Health Auto Export is closed, so
   opening the app for the export also sends the file.
2. **GitHub Actions** (`.github/workflows/process-upload.yml`) runs on every
   push that adds a CSV to `incoming/`: ingest → dashboard → reports, then
   commits `reports/`, `data/`, `dashboard/` and `incoming/processed/` back
   to `main`. See the repo's **Actions** tab for runs.

**Shortcut setup**: open the `.shortcut` file on the iPhone → Add Shortcut.
On import it asks for a fine-grained GitHub token (only `hr-mon`,
*Contents: Read and write*) and the folder (iCloud Drive → Health Auto
Export → Daily hr). The token stays on the phone. Then Shortcuts →
Automation → + → App → Health Auto Export → *Is Closed* → Run Immediately →
this shortcut. `shortcut/build_shortcut.py` regenerates the file (macOS).

After the workflow runs, `git pull` before working locally.

## Report page

**https://github.com/eshwarpotturi/hr-mon/tree/main/reports**: private
(sign in as the repo owner), regenerated after every upload. Latest day vs
your usual, this week vs last week, trend charts, highlights and every day
compared with your overall average.

## Running by hand

```bash
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
│   ├── README.md          <- the report page: charts, comparisons, highlights
│   ├── daily_stats.csv    <- one row per day (avg/min/max/resting/stdev/samples/7-day avg)
│   └── YYYY-MM-DD.md      <- one summary per day
├── scripts/
│   ├── ingest.py             <- merges incoming/*.csv into data/heart_rate_master.csv
│   ├── build_dashboard.py    <- reads the master csv, writes dashboard/index.html
│   ├── report.py             <- reads the master csv, writes reports/
│   ├── update_dashboard.py   <- runs ingest, build_dashboard, report in order
│   └── generate_sample_data.py  <- fake data in the old single-column format (no longer ingested)
├── shortcut/          <- the iPhone upload Shortcut + its builder
└── .github/workflows/process-upload.yml  <- processes uploads on GitHub
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
