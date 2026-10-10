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


def test_runs_of_no_station_join_the_one_they_touch(tmp_path):
    """A run of a ski area the app doesn't list (or of none) is added to the
    station it touches -- directly or through another such run -- and its km
    to the station's stats; one far away is left out."""
    db_path = build_db(tmp_path)
    docs = make_docs(tmp_path, db_path)
    conn = database.connect(db_path)

    def add_run(rid, coords, length):
        geom = json.dumps({"type": "LineString", "coordinates": coords})
        conn.execute("INSERT INTO runs (id, name, status, difficulty, uses, geometry_json, length_m) "
                     "VALUES (?, ?, 'operating', 'easy', 'downhill', ?, ?)", (rid, rid, geom, length))
    # run-1 starts at (10.96, 46.96): ~110 m away, then a second one ~50 m on (~150 m
    # from the station itself, but reached through the first), and one ~5 km off.
    add_run("orphan-near", [[10.9614, 46.9600, 2100], [10.9630, 46.9600, 2000]], 120)
    add_run("orphan-chain", [[10.9636, 46.9600, 1990], [10.9660, 46.9600, 1900]], 180)
    add_run("orphan-far", [[11.03, 46.96, 2000], [11.04, 46.96, 1900]], 760)
    conn.commit()

    assert run(db_path, docs) == 0
    rec = json.loads((docs / "data" / "skiarea-1.json").read_text())
    names = [r["name"] for r in rec["runs"]]
    assert "orphan-near" in names and "orphan-chain" in names and "orphan-far" not in names
    easy = next(s for s in rec["run_stats"] if s["activity"] == "downhill" and s["difficulty"] == "easy")
    assert easy["run_count"] >= 2 and easy["length_km"] >= 0.3
    # Run again on the same data: nothing changes.
    before = (docs / "data" / "skiarea-1.json").read_text()
    assert run(db_path, docs) == 0
    assert (docs / "data" / "skiarea-1.json").read_text() == before
