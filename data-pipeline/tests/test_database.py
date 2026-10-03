from __future__ import annotations

from pathlib import Path

import pytest

from ski_pipeline import database, transform

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def conn(tmp_path):
    connection = database.connect(tmp_path / "ski_info.db")
    database.create_schema(connection)
    yield connection
    connection.close()


def test_create_schema_creates_expected_tables(conn):
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {
        "ski_areas",
        "ski_area_run_stats",
        "ski_area_lift_stats",
        "runs",
        "run_ski_areas",
        "lifts",
        "lift_ski_areas",
    }.issubset(tables)


def test_insert_and_query_ski_area_with_stats(conn):
    features = list(transform.iter_features(FIXTURES / "ski_areas.sample.geojson"))
    ski_area_rows = [transform.transform_ski_area(f) for f in features]
    run_stats_rows = [row for f in features for row in transform.transform_ski_area_run_stats(f)]
    lift_stats_rows = [row for f in features for row in transform.transform_ski_area_lift_stats(f)]

    database.insert_ski_areas(conn, ski_area_rows)
    database.insert_ski_area_run_stats(conn, run_stats_rows)
    database.insert_ski_area_lift_stats(conn, lift_stats_rows)
    conn.commit()

    name = conn.execute("SELECT name FROM ski_areas WHERE id = ?", ("skiarea-1",)).fetchone()[0]
    assert name == "Sample Resort"

    easy_km = conn.execute(
        "SELECT length_km FROM ski_area_run_stats WHERE ski_area_id = ? AND difficulty = ?",
        ("skiarea-1", "easy"),
    ).fetchone()[0]
    assert easy_km == 15.2

    gondola_count = conn.execute(
        "SELECT lift_count FROM ski_area_lift_stats WHERE ski_area_id = ? AND lift_type = ?",
        ("skiarea-1", "gondola"),
    ).fetchone()[0]
    assert gondola_count == 3


def test_insert_runs_and_links(conn):
    # A ski area row must exist first to satisfy the foreign key on run_ski_areas.
    database.insert_ski_areas(conn, [{
        "id": "skiarea-1", "name": "Sample Resort", "status": "operating",
        "activities": "downhill", "run_convention": "europe", "country_code": "AT",
        "region": "Tyrol", "locality": "Sample Village", "latitude": 46.9658,
        "longitude": 10.9646, "min_elevation_m": 1350, "max_elevation_m": 3340,
        "wikidata_id": "Q123456", "websites": "[]",
    }])

    run_rows, link_rows = [], []
    for feature in transform.iter_features(FIXTURES / "runs.sample.geojson"):
        row, ski_area_ids = transform.transform_run(feature)
        run_rows.append(row)
        link_rows.extend({"run_id": row["id"], "ski_area_id": sa} for sa in ski_area_ids)

    database.insert_runs(conn, run_rows)
    database.insert_run_ski_areas(conn, link_rows)
    conn.commit()

    total_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert total_runs == 3

    linked_runs = conn.execute(
        "SELECT run_id FROM run_ski_areas WHERE ski_area_id = 'skiarea-1' ORDER BY run_id"
    ).fetchall()
    assert [r[0] for r in linked_runs] == ["run-1", "run-2"]

    descent = conn.execute("SELECT descent_m FROM runs WHERE id = 'run-1'").fetchone()[0]
    assert descent == 100.0


def test_insert_lifts_and_links(conn):
    database.insert_ski_areas(conn, [{
        "id": "skiarea-1", "name": "Sample Resort", "status": "operating",
        "activities": "downhill", "run_convention": "europe", "country_code": "AT",
        "region": "Tyrol", "locality": "Sample Village", "latitude": 46.9658,
        "longitude": 10.9646, "min_elevation_m": 1350, "max_elevation_m": 3340,
        "wikidata_id": "Q123456", "websites": "[]",
    }])

    lift_rows, link_rows = [], []
    for feature in transform.iter_features(FIXTURES / "lifts.sample.geojson"):
        row, ski_area_ids = transform.transform_lift(feature)
        lift_rows.append(row)
        link_rows.extend({"lift_id": row["id"], "ski_area_id": sa} for sa in ski_area_ids)

    database.insert_lifts(conn, lift_rows)
    database.insert_lift_ski_areas(conn, link_rows)
    conn.commit()

    capacity = conn.execute("SELECT capacity FROM lifts WHERE id = 'lift-1'").fetchone()[0]
    assert capacity == 2400

    linked = conn.execute(
        "SELECT COUNT(*) FROM lift_ski_areas WHERE ski_area_id = 'skiarea-1'"
    ).fetchone()[0]
    assert linked == 2


def test_insert_is_idempotent_on_rerun(conn):
    row = {
        "id": "skiarea-1", "name": "Sample Resort", "status": "operating",
        "activities": "downhill", "run_convention": "europe", "country_code": "AT",
        "region": "Tyrol", "locality": "Sample Village", "latitude": 46.9658,
        "longitude": 10.9646, "min_elevation_m": 1350, "max_elevation_m": 3340,
        "wikidata_id": "Q123456", "websites": "[]",
    }
    database.insert_ski_areas(conn, [row])
    database.insert_ski_areas(conn, [row])
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM ski_areas").fetchone()[0]
    assert count == 1
