# Heart Rate Monitor — MVP

A local pipeline: Apple Watch → Health app → Health Auto Export (iPhone app) →
CSV in this folder → trend dashboard, fully offline, no cloud service involved.

## Your actual Health Auto Export automation

Based on the automation config you have set up (`automationExportBaseName: "Hr"`):

- **Export type**: `healthMetrics` — one **wide CSV per day** with a column per
  metric (not one file per metric), aligned by minute-level timestamp.
- **Destination**: iCloud Drive
- **Aggregation**: Minutes, one file per day
- **Metrics included**: Walking Step Length, Walking Speed, Walking Heart Rate
  Average, Walking+Running Distance, Time in Daylight, Step Count,
  **Resting Heart Rate**, Respiratory Rate, Physical Effort, Heart Rate
  Variability, **Heart Rate**, Blood Pressure, Apple Stand/Move/Exercise Time
- **Trigger**: a daily reminder notification at 9:00pm (`minuteOfDay: 1260`) to
  open the app and run the export — Health Auto Export needs the app opened to
  actually run on the free tier, so treat that 9pm notification as your cue to
  open the app once a day.
- Files will be named like `Hr-2026-09-27.csv` (or similar, based on your base
  name) and land in whatever iCloud Drive folder you pointed the automation at.

**Important**: because this export bundles 15 metrics into one file, several
column names all contain the words "heart rate" — `Walking Heart Rate
Average`, `Resting Heart Rate`, `Heart Rate Variability`, and plain `Heart
Rate`. The ingestion script (`ingest.py`) specifically matches the exact
normalized column name (stripping the trailing unit, e.g. `(count/min)`) so it
never confuses these — it only pulls `Heart Rate` and `Resting Heart Rate`,
ignoring the others. This was tested against a synthetic file with the exact
same column layout and order as your real automation before being pointed at
this folder.

## Folder layout

```
hr-mon/
├── incoming/          <- Health Auto Export's CSV should end up here
│   └── processed/     <- ingest.py archives files here once merged
├── data/
│   └── heart_rate_master.csv   <- running, deduped dataset: timestamp, heart_rate, resting_heart_rate
├── dashboard/
│   └── index.html     <- open this in a browser; regenerated each run
├── scripts/
│   ├── ingest.py             <- merges incoming/*.csv into data/heart_rate_master.csv
│   ├── build_dashboard.py    <- reads the master csv, writes dashboard/index.html
│   ├── update_dashboard.py   <- runs both of the above, in order
│   └── generate_sample_data.py  <- creates realistic fake test data (delete once real data flows)
└── README.md
```

## Getting real data into this folder

Health Auto Export saves to iCloud Drive, but this Mac session only has access
to `/Users/Pothuri/Desktop/cc/hr-mon`. So each day, once the export lands in
your iCloud Drive folder:

- **For now (MVP, manual)**: drag/copy that day's CSV from your iCloud Drive
  folder into `hr-mon/incoming/`, then run:
  ```bash
  cd hr-mon
  python3 scripts/update_dashboard.py
  open dashboard/index.html
  ```
- **Later (automation)**: once this is validated with a few real days, we can
  set up a small script (cron/launchd, or a Shortcuts automation) that copies
  new files from the iCloud folder into `incoming/` and runs the update
  automatically — this is the "figure out how to increase automation" step
  we agreed to come back to.

## Testing right now with fake data

Since real Apple Watch exports aren't confirmed flowing yet, generate 14 days
of realistic synthetic data — reproducing your exact automation's column
layout, including the heart-rate-like decoy columns — to see the whole
pipeline work end-to-end:

```bash
cd hr-mon
python3 scripts/generate_sample_data.py
python3 scripts/update_dashboard.py
open dashboard/index.html
```

Once real exports start arriving, delete the synthetic CSVs from
`incoming/processed/` and `data/heart_rate_master.csv` and start fresh — or
leave them; the dashboard will just show a longer history with a few fake
days at the start.

## Design notes / known limitations (MVP)

- **Sampling density**: Apple Watch's default background HR sampling is
  roughly every 5–10 minutes at rest, much more often when moving. This
  dashboard works fine with that — daily trends don't need minute-level
  resolution. (We deliberately ruled out forcing denser sampling via a
  background Workout session — not worth the battery cost.)
- **Resting HR**: uses Apple's own `Resting Heart Rate` reading for days where
  your export includes one (this is a real Apple-computed value, appearing
  once per day). For any day where it's missing, the dashboard falls back to
  an approximation (mean of the lowest ~10% of that day's Heart Rate samples)
  and marks it with a `~` in the table so you always know which kind you're
  looking at.
- **No automation yet.** Right now you run `update_dashboard.py` by hand,
  after manually moving the day's export into `incoming/`. Automating both
  the file move and the daily run is the next step once this is validated.
