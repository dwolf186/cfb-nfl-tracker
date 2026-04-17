# CFB → NFL Talent Tracker

Which college football programs, in which years, produced the most future NFL players?

**Live site:** <https://dwolf186.github.io/cfb-nfl-tracker/>

This project combines **nflverse** active-roster data with final AP Top 25 rankings to rank FBS programs by NFL talent output.

## Stack

- **Pipeline:** Python 3 + pandas — downloads nflverse CSVs, normalizes college names, cross-references AP Top 25, writes JSON + CSV outputs.
- **Frontend:** Plain HTML + vanilla JS + Chart.js (CDN). No build step.
- **Serving:** Static files. Open `web/index.html` directly or serve with `python -m http.server`.

## Install

```
pip install -r requirements.txt
```

## Build the dataset

```
# Full pipeline (downloads + caches everything on first run)
python -m pipeline.cli

# One year, for testing
python -m pipeline.cli --year 2014

# Force re-download of nflverse CSVs
python -m pipeline.cli --refresh-cache

# Use cached CSVs only (no network)
python -m pipeline.cli --skip-fetch
```

Outputs:
- `data/output/cfb_nfl_talent.csv` — canonical dataset (one row per college-season)
- `web/data/*.json` — consumed by the frontend
- `data/logs/unmatched_colleges.log` — raw college strings the normalizer didn't recognize; review periodically and extend `pipeline/college_name_map.json`

## View the site

```
cd web
python -m http.server 8000
# then open http://localhost:8000
```

Views: Leaderboard, Year, Program Detail, Head-to-Head. Global filters (year range, AP-rank threshold, metric) live in the URL hash.

## Deploy

The site is hosted on **GitHub Pages** via the workflow at
[.github/workflows/deploy.yml](.github/workflows/deploy.yml). Every push to
`main` uploads the contents of `web/` as a Pages artifact and publishes it.
To refresh the NFL/AP data:

```
python -m pipeline.cli
git add web/data data/output
git commit -m "data: refresh NFL rosters + AP polls"
git push
```

Deploy takes ~1 minute. Status: <https://github.com/dwolf186/cfb-nfl-tracker/actions>

## Data caveats

See the footer in-app. Summary:

1. College name matching is approximate.
2. Pre-2015 roster CSVs often omit `college`; backfilled from the nflverse `players.csv` + `draft_picks.csv`. Coverage is ≥99% all years.
3. Undrafted free agents included when they appear on a 53-man active roster.
4. Practice-squad players excluded by design.
5. AP poll data is auto-fetched when possible; hardcoded fallback is **unverified** and should be audited against official archives.
6. College-season year is estimated for players without exact roster data (simplification option from PRD).
