# Ski Info — data pipeline

Downloads OpenSkiMap's daily GeoJSON exports (ski areas, runs, lifts) and
loads them into a local SQLite database the mobile app can embed.

Source: [OpenSkiMap](https://openskimap.org), format documented in
[`openskidata-format`](https://github.com/russellporter/openskidata-format).
Licensed under [ODbL](https://opendatacommons.org/licenses/odbl/) — the app
must attribute OpenStreetMap/OpenSkiMap.

## Setup

```bash
cd data-pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Run it

```bash
python -m ski_pipeline.cli --db data/ski_info.db -v
```

This downloads `ski_areas.geojson`, `runs.geojson` and `lifts.geojson` into
`./data` (skipping any that already exist — pass `--force-download` to
refresh) and builds `data/ski_info.db`. Runs and lifts are streamed and
written in batches, so memory use stays bounded regardless of dataset size
(as of writing: ~7,000 alpine ski areas, ~230,000 run segments).

Useful flags:
- `--skip-download` — reuse GeoJSON files already in `--data-dir` (fast
  iteration on the transform/database code without re-downloading).
- `--force-download` — re-download even if the files are already there.
- `--data-dir PATH` / `--db PATH` — change where files and the database go.

## Tests

```bash
pytest
```

Tests run against small hand-written GeoJSON fixtures in
`tests/fixtures/` (matching the real `openskidata-format` schema), so they
don't need network access or the full ~hundreds-of-MB dataset.

## What ends up in the database

See `sql/schema.sql` for the full schema. In short:

- **`ski_areas`** — name, location, status, and min/max elevation.
- **`ski_area_run_stats`** / **`ski_area_lift_stats`** — km of piste and
  lift count/length per ski area, broken down by difficulty / lift type.
  These come precomputed from OpenSkiMap.
- **`runs`** — one row per piste segment: difficulty, grooming, snowmaking,
  lit/gladed/patrolled flags, plus **length, ascent/descent and real pitch
  in %** computed in `geometry.py` from the run's 3D coordinates (not just
  the coarse difficulty tag).
- **`lifts`** — type, capacity, occupancy, ride duration, detachable/bubble/
  heating flags, plus computed length and vertical.
- **`run_ski_areas`** / **`lift_ski_areas`** — a run or lift can belong to
  more than one ski area (shared lift/piste systems), so these are
  many-to-many link tables rather than a foreign key on `runs`/`lifts`.

Not in this dataset: lift ticket prices, editorial ratings, season/opening
dates, or live snow/weather. See the repo root README for why, and the plan
to curate those separately for the most-visited resorts.
