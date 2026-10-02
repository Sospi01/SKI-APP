from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from ski_pipeline import database

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import add_stations  # noqa: E402
from tests.test_refresh_stations import build_db  # noqa: E402


def us_db(tmp_path: Path) -> Path:
    db_path = build_db(tmp_path)
    conn = database.connect(db_path)
    conn.execute("UPDATE ski_areas SET country_code = 'US'")
    conn.commit()
    return db_path


def empty_docs(tmp_path: Path, catalogue: list[dict]) -> Path:
    docs = tmp_path / "docs"
    (docs / "data").mkdir(parents=True)
    (docs / "stations.js").write_text("// catalogue\nvar STATIONS = " + json.dumps(catalogue) + ";\nvar STATION_GROUPS = [];\n")
    return docs


def run(db_path: Path, docs: Path, *extra: str) -> int:
    sys.argv = ["add_stations.py", "--db", str(db_path), "--docs", str(docs), "--country", "US", "--min-km", "0", *extra]
    return add_stations.main()


def catalogue(docs: Path) -> list[dict]:
    return add_stations.read_catalogue(docs / "stations.js")[2]


def area(db_path: Path, sid: str) -> sqlite3.Row:
    conn = database.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn.execute("SELECT * FROM ski_areas WHERE id = ?", (sid,)).fetchone()


def test_adds_missing_areas_with_runs_and_lifts(tmp_path):
    db_path = us_db(tmp_path)
    docs = empty_docs(tmp_path, [])
    assert run(db_path, docs) == 0
    added = catalogue(docs)
    assert [s["id"] for s in added] == ["skiarea-1"]  # skiarea-2 has no runs or lifts
    record = json.loads((docs / "data" / "skiarea-1.json").read_text())
    assert record["services"] == [] and record["runs"] and record["lifts"]
    assert added[0]["country"] == "US" and added[0]["pisteKm"] > 0
    assert (docs / "stations.js").read_text().endswith("var STATION_GROUPS = [];\n")


def test_dry_run_writes_nothing(tmp_path):
    db_path = us_db(tmp_path)
    docs = empty_docs(tmp_path, [])
    before = (docs / "stations.js").read_text()
    assert run(db_path, docs, "--dry-run") == 0
    assert (docs / "stations.js").read_text() == before
    assert not list((docs / "data").glob("*.json"))


def test_skips_stations_already_in_the_app_or_right_next_to_one(tmp_path):
    db_path = us_db(tmp_path)
    a = area(db_path, "skiarea-1")
    # Same id: already there.
    docs = empty_docs(tmp_path, [{"id": "skiarea-1", "name": "Sample Resort", "region": None, "pisteKm": 1,
                                  "country": "US", "lat": a["latitude"], "lon": a["longitude"]}])
    assert run(db_path, docs) == 0
    assert len(catalogue(docs)) == 1
    # Another id 500 m away: the same area under a different id.
    docs2 = empty_docs(tmp_path / "b", [{"id": "other", "name": "Old Sample", "region": None, "pisteKm": 1,
                                         "country": "US", "lat": a["latitude"] + 0.0045, "lon": a["longitude"]}])
    assert run(db_path, docs2) == 0
    assert [s["id"] for s in catalogue(docs2)] == ["other"]


def test_skips_a_small_part_of_a_bigger_station_nearby(tmp_path):
    db_path = us_db(tmp_path)
    a = area(db_path, "skiarea-1")
    # A station 50 times bigger 2.5 km away: skiarea-1 is a part of it.
    docs = empty_docs(tmp_path, [{"id": "big", "name": "Big Resort", "region": None, "pisteKm": 5000,
                                  "country": "US", "lat": a["latitude"] + 0.0225, "lon": a["longitude"]}])
    assert run(db_path, docs) == 0
    assert [s["id"] for s in catalogue(docs)] == ["big"]
