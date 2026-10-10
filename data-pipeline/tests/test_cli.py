from __future__ import annotations

import shutil
from pathlib import Path

from ski_pipeline import cli, database

FIXTURES = Path(__file__).parent / "fixtures"


def test_main_builds_database_from_local_files_without_downloading(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shutil.copy(FIXTURES / "ski_areas.sample.geojson", data_dir / "ski_areas.geojson")
    shutil.copy(FIXTURES / "runs.sample.geojson", data_dir / "runs.geojson")
    shutil.copy(FIXTURES / "lifts.sample.geojson", data_dir / "lifts.geojson")

    db_path = tmp_path / "ski_info.db"

    cli.main([
        "--data-dir", str(data_dir),
        "--db", str(db_path),
        "--skip-download",
    ])

    assert db_path.exists()

    conn = database.connect(db_path)
    try:
        ski_area_count = conn.execute("SELECT COUNT(*) FROM ski_areas").fetchone()[0]
        run_count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        lift_count = conn.execute("SELECT COUNT(*) FROM lifts").fetchone()[0]

        assert ski_area_count == 2
        assert run_count == 3
        assert lift_count == 2

        easy_km = conn.execute(
            "SELECT length_km FROM ski_area_run_stats WHERE ski_area_id = 'skiarea-1' AND difficulty = 'easy'"
        ).fetchone()[0]
        assert easy_km == 15.2
    finally:
        conn.close()


def test_main_rerun_is_idempotent(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shutil.copy(FIXTURES / "ski_areas.sample.geojson", data_dir / "ski_areas.geojson")
    shutil.copy(FIXTURES / "runs.sample.geojson", data_dir / "runs.geojson")
    shutil.copy(FIXTURES / "lifts.sample.geojson", data_dir / "lifts.geojson")

    db_path = tmp_path / "ski_info.db"
    args = ["--data-dir", str(data_dir), "--db", str(db_path), "--skip-download"]

    cli.main(args)
    cli.main(args)

    conn = database.connect(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM ski_areas").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 3
    finally:
        conn.close()
