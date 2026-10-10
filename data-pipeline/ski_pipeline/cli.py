"""Command-line entry point: download OpenSkiMap sources and build the SQLite database."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import config, database, download, transform

logger = logging.getLogger(__name__)


def build_database(data_dir: Path, db_path: Path, *, batch_size: int = 2000) -> None:
    """Load ski_areas/runs/lifts.geojson from `data_dir` into a fresh SQLite database.

    Ski areas are loaded fully in memory (there are a few thousand of them),
    but runs and lifts are streamed and written in batches so memory stays
    bounded regardless of dataset size.
    """
    conn = database.connect(db_path)
    database.create_schema(conn)

    ski_area_rows, run_stats_rows, lift_stats_rows = [], [], []
    for feature in transform.iter_features(data_dir / "ski_areas.geojson"):
        ski_area_rows.append(transform.transform_ski_area(feature))
        run_stats_rows.extend(transform.transform_ski_area_run_stats(feature))
        lift_stats_rows.extend(transform.transform_ski_area_lift_stats(feature))
    database.insert_ski_areas(conn, ski_area_rows)
    database.insert_ski_area_run_stats(conn, run_stats_rows)
    database.insert_ski_area_lift_stats(conn, lift_stats_rows)
    conn.commit()
    logger.info("Loaded %d ski areas", len(ski_area_rows))

    run_count = 0
    run_rows, run_links = [], []
    for feature in transform.iter_features(data_dir / "runs.geojson"):
        row, ski_area_ids = transform.transform_run(feature)
        run_rows.append(row)
        run_links.extend({"run_id": row["id"], "ski_area_id": sa} for sa in ski_area_ids)
        if len(run_rows) >= batch_size:
            database.insert_runs(conn, run_rows)
            database.insert_run_ski_areas(conn, run_links)
            conn.commit()
            run_count += len(run_rows)
            run_rows, run_links = [], []
    database.insert_runs(conn, run_rows)
    database.insert_run_ski_areas(conn, run_links)
    conn.commit()
    run_count += len(run_rows)
    logger.info("Loaded %d runs", run_count)

    lift_count = 0
    lift_rows, lift_links = [], []
    for feature in transform.iter_features(data_dir / "lifts.geojson"):
        row, ski_area_ids = transform.transform_lift(feature)
        lift_rows.append(row)
        lift_links.extend({"lift_id": row["id"], "ski_area_id": sa} for sa in ski_area_ids)
        if len(lift_rows) >= batch_size:
            database.insert_lifts(conn, lift_rows)
            database.insert_lift_ski_areas(conn, lift_links)
            conn.commit()
            lift_count += len(lift_rows)
            lift_rows, lift_links = [], []
    database.insert_lifts(conn, lift_rows)
    database.insert_lift_ski_areas(conn, lift_links)
    conn.commit()
    lift_count += len(lift_rows)
    logger.info("Loaded %d lifts", lift_count)

    conn.close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="ski-pipeline",
        description="Download OpenSkiMap's ski area/run/lift data and build a local SQLite database.",
    )
    parser.add_argument("--data-dir", type=Path, default=config.DEFAULT_DATA_DIR, help="Where source GeoJSON files are stored")
    parser.add_argument("--db", type=Path, default=config.DEFAULT_DB_PATH, help="Output SQLite database path")
    parser.add_argument("--force-download", action="store_true", help="Re-download source files even if already present")
    parser.add_argument("--skip-download", action="store_true", help="Reuse existing files in --data-dir without downloading")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if not args.skip_download:
        download.download_all(args.data_dir, force=args.force_download)

    build_database(args.data_dir, args.db)
    logger.info("Database ready at %s", args.db)


if __name__ == "__main__":
    main()
