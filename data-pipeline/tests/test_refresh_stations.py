from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path

from ski_pipeline import cli, database

FIXTURES = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import refresh_stations  # noqa: E402


def build_db(tmp_path: Path) -> Path:
    data_dir = tmp_path / "osm"
    data_dir.mkdir()
    for kind in ("ski_areas", "runs", "lifts"):
        shutil.copy(FIXTURES / f"{kind}.sample.geojson", data_dir / f"{kind}.geojson")
    db_path = tmp_path / "ski_info.db"
    cli.main(["--data-dir", str(data_dir), "--db", str(db_path), "--skip-download"])
    return db_path


def make_docs(tmp_path: Path, db_path: Path) -> Path:
    """docs/ as the app has it: one data file per ski area (plus services) and the catalogue."""
    docs = tmp_path / "docs"
    (docs / "data").mkdir(parents=True)
    conn = database.connect(db_path)
    conn.row_factory = sqlite3.Row
    ids = [r[0] for r in conn.execute("SELECT id FROM ski_areas ORDER BY id")]
    catalogue = []
    for sid in ids:
        record = refresh_stations.station_record(conn, sid)
        record["services"] = [{"category": "restaurant", "lat": 1.0, "lon": 2.0, "name": "Hut"}]
        (docs / "data" / f"{sid}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        catalogue.append({"id": sid, "name": record["name"], "region": record["region"], "pisteKm": 0, "country": "ES"})
    (docs / "stations.js").write_text("// catalogue\nvar STATIONS = " + json.dumps(catalogue) + ";\nvar STATION_GROUPS = [];\n")
    return docs


def run(db_path: Path, docs: Path) -> int:
    sys.argv = ["refresh_stations.py", "--db", str(db_path), "--docs", str(docs)]
    return refresh_stations.main()


def test_unchanged_data_rewrites_nothing(tmp_path):
    db_path = build_db(tmp_path)
    docs = make_docs(tmp_path, db_path)
    before = {p.name: p.read_text() for p in (docs / "data").glob("*.json")}
    assert run(db_path, docs) == 0
    assert {p.name: p.read_text() for p in (docs / "data").glob("*.json")} == before


def test_changes_are_applied_and_services_kept(tmp_path):
    db_path = build_db(tmp_path)
    docs = make_docs(tmp_path, db_path)
    conn = database.connect(db_path)
    conn.execute("UPDATE ski_areas SET name = 'Renamed' WHERE id = 'skiarea-1'")
    conn.commit()
    assert run(db_path, docs) == 0
    record = json.loads((docs / "data" / "skiarea-1.json").read_text())
    assert record["name"] == "Renamed"
    assert record["services"][0]["name"] == "Hut"
    assert '"name":"Renamed"' in (docs / "stations.js").read_text()


def test_broken_data_is_not_written(tmp_path):
    db_path = build_db(tmp_path)
    docs = make_docs(tmp_path, db_path)
    before = {p.name: p.read_text() for p in (docs / "data").glob("*.json")}
    conn = database.connect(db_path)
    for table in ("run_ski_areas", "lift_ski_areas", "ski_area_run_stats", "ski_area_lift_stats", "ski_areas"):
        conn.execute(f"DELETE FROM {table}")  # every station missing: an OpenSkiMap problem, not real closures
    conn.commit()
    assert run(db_path, docs) == 1
    assert {p.name: p.read_text() for p in (docs / "data").glob("*.json")} == before


def test_station_with_a_new_openskimap_id_is_found_and_keeps_its_id(tmp_path):
    db_path = build_db(tmp_path)
    docs = make_docs(tmp_path, db_path)
    conn = sqlite3.connect(db_path)  # plain connection: rename the id across tables
    for table, col in (("ski_areas", "id"), ("run_ski_areas", "ski_area_id"), ("lift_ski_areas", "ski_area_id"),
                       ("ski_area_run_stats", "ski_area_id"), ("ski_area_lift_stats", "ski_area_id")):
        conn.execute(f"UPDATE {table} SET {col} = 'skiarea-new' WHERE {col} = 'skiarea-1'")
    conn.execute("UPDATE ski_areas SET name = 'Renamed' WHERE id = 'skiarea-new'")
    conn.commit()
    assert run(db_path, docs) == 0
    record = json.loads((docs / "data" / "skiarea-1.json").read_text())
    assert record["id"] == "skiarea-1" and record["name"] == "Renamed"
    assert all(s["ski_area_id"] == "skiarea-1" for s in record["run_stats"])
    assert not (docs / "data" / "skiarea-new.json").exists()


def test_float_noise_is_not_a_change(tmp_path):
    db_path = build_db(tmp_path)
    docs = make_docs(tmp_path, db_path)
    before = {p.name: p.read_text() for p in (docs / "data").glob("*.json")}
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE ski_areas SET latitude = latitude + 1e-13")
    conn.execute("UPDATE ski_area_run_stats SET length_km = length_km + 1e-13")
    conn.commit()
    assert run(db_path, docs) == 0
    assert {p.name: p.read_text() for p in (docs / "data").glob("*.json")} == before
