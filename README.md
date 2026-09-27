# Heart Rate Monitor — MVP

A local pipeline: Apple Watch → Health app → Health Auto Export (iPhone app) →
CSV in this folder → trend dashboard, fully offline, no cloud service involved.

## Folder layout

```
hr-mon/
├── incoming/          <- Health Auto Export drops daily CSVs here
│   └── processed/     <- ingest.py archives files here once merged
├── data/
│   └── heart_rate_master.csv   <- the running, deduped dataset
├── dashboard/
│   └── index.html     <- open this in a browser; regenerated each run
├── scripts/
│   ├── ingest.py             <- merges incoming/*.csv into data/heart_rate_master.csv
│   ├── build_dashboard.py    <- reads the master csv, writes dashboard/index.html
│   ├── update_dashboard.py   <- runs both of the above, in order
│   └── generate_sample_data.py  <- creates fake test data (delete once real data flows)
└── README.md
```

## One-time setup on your iPhone

1. Install **Health Auto Export** from the App Store (free tier is enough for CSV export).
2. In the app, create an **Automation**:
   - Data type: **Heart Rate**
   - Format: **CSV**
   - Frequency: **Daily** (e.g. run at 11:59pm, or whenever you like)
   - Destination: **iCloud Drive** → point it at a folder — create one named
     e.g. `HR-Export` inside iCloud Drive.
3. On your Mac, that same iCloud Drive folder will sync automatically (Finder →
   iCloud Drive → HR-Export). You don't need to do anything else for the sync
   itself — Apple handles it.
4. Because this Mac session only has access to `/Users/Pothuri/Desktop/cc/hr-mon`,
   **move or symlink** the synced export folder so its CSVs land in
   `hr-mon/incoming/`. Easiest option: point Health Auto Export directly at
   `iCloud Drive/HR-Export`, then either:
   - drag the daily CSV into `hr-mon/incoming/` yourself each day (simplest,
     zero setup), or
   - later, set up a small `launchd`/cron job or a Shortcuts automation that
     copies new files from the iCloud folder into `hr-mon/incoming/`
     automatically (this is the "figure out how to increase automation" step
     for later, as agreed).

## Running it (MVP — manual, once a day)

```bash
cd hr-mon
python3 scripts/update_dashboard.py
open dashboard/index.html
```

This ingests any new CSVs sitting in `incoming/`, updates
`data/heart_rate_master.csv`, and regenerates `dashboard/index.html`.

## Testing right now with fake data

Since real Apple Watch exports aren't flowing yet, generate 14 days of
realistic synthetic heart-rate data to see the whole pipeline work
end-to-end:

```bash
cd hr-mon
python3 scripts/generate_sample_data.py
python3 scripts/update_dashboard.py
open dashboard/index.html
```

Once real exports start arriving, delete the synthetic CSVs from
`incoming/processed/` and `data/heart_rate_master.csv` and start fresh —
or just leave them; the dashboard will just show a longer history that
includes a few fake days at the start.

## Design notes / known limitations (MVP)

- **Sampling density**: Apple Watch's default background HR sampling is
  roughly every 5–10 minutes at rest, much more often when moving. This
  dashboard works fine with that — daily trends don't need minute-level
  resolution. (We deliberately ruled out forcing denser sampling via a
  background Workout session — not worth the battery cost.)
- **"Resting HR" shown here is an approximation** — the mean of the lowest
  ~10% of a day's samples — not Apple's own resting-HR algorithm (which
  uses stricter criteria). Good enough for trend-watching, not a medical
  reading.
- **No automation yet.** Right now you run `update_dashboard.py` by hand.
  Once the pipeline is validated with a few real days of data, the next
  step is scheduling it (cron, launchd, or a Shortcuts automation) so it
  updates itself daily without you touching anything.
