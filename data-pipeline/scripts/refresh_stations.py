"""Refresh the stations already in the app from a new OpenSkiMap database.

Run weekly by .github/workflows/refresh-stations.yml after the database is
rebuilt (python -m ski_pipeline.cli), so that fixes people make in
OpenStreetMap reach the app. For every docs/data/<id>.json it re-exports the
ski area's runs, lifts and stats with the same query the original fetch used
(fetch-stations.yml), keeps what doesn't come from OpenSkiMap (the Overpass
"services"), and updates the station's entry in docs/stations.js.

It never adds or removes stations (that stays a reviewed, manual step), and
it is deliberately conservative:
  - a station missing from the new data, or whose downhill runs or km drop by
    more than half, keeps its current file (and is listed in the report);
  - if that happens to more than MAX_SKIPPED_SHARE of all stations, the new
    data is assumed broken and nothing is written at all;
  - files are only rewritten when their content actually changed.

Runs and lifts that belong to no station of the app (mapped as part of a
small ski area that was left out because it's really a corner of a bigger
one -- the Cesana side of Sansicario, in the Vía Láctea -- or of no ski area
at all) are added to the station they touch: within ORPHAN_NEAR_M of it,
directly or through other such runs and lifts (ORPHAN_LINK_M apart).

Usage: python3 data-pipeline/scripts/refresh_stations.py --db data-pipeline/data/ski_info.db
"""
from __future__ import annotations

import argparse
import json
import os
import math
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MAX_SKIPPED_SHARE = 0.2
MIN_KEEP_RATIO = 0.5
ORPHAN_NEAR_M = 300
ORPHAN_LINK_M = 60
RUN_COLUMNS = """r.name, r.ref, r.difficulty, r.uses, r.grooming, r.gladed,
               r.lit, r.snowmaking, r.patrolled,
               r.geometry_json, r.length_m, r.ascent_m, r.descent_m, r.vertical_m,
               r.min_elevation_m, r.max_elevation_m, r.avg_pitch_percent, r.max_pitch_percent"""
RUN_FILTER = "(r.status IS NULL OR r.status = 'operating') AND (r.uses IS NULL OR r.uses LIKE '%downhill%')"
LIFT_COLUMNS = """l.name, l.ref, l.lift_type, l.access, l.capacity, l.occupancy,
               l.duration_s, l.detachable, l.bubble, l.heating,
               l.geometry_json, l.length_m, l.vertical_m"""
LIFT_FILTER = "(l.status IS NULL OR l.status = 'operating')"
# Key order of the data files, as first written.
KEYS = ["id", "name", "status", "activities", "run_convention", "country_code", "region", "locality", "latitude",
        "longitude", "min_elevation_m", "max_elevation_m", "wikidata_id", "websites", "run_stats", "lift_stats",
        "runs", "lifts"]


def simplify_geometry(geometry_json: str | None):
    """[[lon, lat, ele], ...] parts, rounded like the original fetch."""
    if not geometry_json:
        return None
    geom = json.loads(geometry_json)
    gtype, coords = geom.get("type"), geom.get("coordinates")
    if gtype == "LineString":
        parts = [coords]
    elif gtype == "MultiLineString":
        parts = coords
    elif gtype == "Polygon":
        parts = coords[:1]
    else:
        return None

    def point(c):
        return [round(c[0], 5), round(c[1], 5), round(c[2], 1)] if len(c) >= 3 else [round(c[0], 5), round(c[1], 5)]
    return [[point(c) for c in part] for part in parts]


def station_record(conn: sqlite3.Connection, area_id: str) -> dict | None:
    """The ski area as the app's data file (without services), or None."""
    def rows(sql, params=()):
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

    found = rows("SELECT * FROM ski_areas WHERE id = ?", (area_id,))
    if not found:
        return None
    area = found[0]
    area["run_stats"] = rows("SELECT * FROM ski_area_run_stats WHERE ski_area_id = ? ORDER BY activity, difficulty", (area_id,))
    area["lift_stats"] = rows("SELECT * FROM ski_area_lift_stats WHERE ski_area_id = ? ORDER BY lift_type", (area_id,))
    area["runs"] = rows(
        f"""
        SELECT {RUN_COLUMNS}
        FROM runs r
        JOIN run_ski_areas rsa ON rsa.run_id = r.id
        WHERE rsa.ski_area_id = ? AND {RUN_FILTER}
        ORDER BY r.difficulty, r.length_m DESC, r.id
        """, (area_id,))
    for r in area["runs"]:
        r["geom"] = simplify_geometry(r.pop("geometry_json"))
    area["lifts"] = rows(
        f"""
        SELECT {LIFT_COLUMNS}
        FROM lifts l
        JOIN lift_ski_areas lsa ON lsa.lift_id = l.id
        WHERE lsa.ski_area_id = ? AND {LIFT_FILTER}
        ORDER BY l.length_m DESC, l.id
        """, (area_id,))
    for l in area["lifts"]:
        l["geom"] = simplify_geometry(l.pop("geometry_json"))
    area["websites"] = json.loads(area.get("websites") or "[]")
    return {k: area.get(k) for k in KEYS}


def _points(item):
    return [c for part in item.get("geom") or [] for c in part]


def absorb_orphans(conn: sqlite3.Connection, records: dict, area_ids: set) -> dict:
    """Add to `records` (app id -> station record) the runs and lifts of no
    station (see the module docstring), with their stats. `area_ids` are the
    OpenSkiMap ski areas the stations come from. Returns app id ->
    (runs added, lifts added, downhill km added)."""
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS app_areas (id TEXT PRIMARY KEY)")
    conn.execute("DELETE FROM app_areas")
    conn.executemany("INSERT OR IGNORE INTO app_areas VALUES (?)", [(i,) for i in area_ids])
    # Where the stations are: 0.05 deg cells (to skip the rest of the world) and
    # ~ORPHAN_NEAR_M cells holding each station's points (for the distance).
    coarse, near = set(), {}
    cell = ORPHAN_NEAR_M / 111_320
    for sid, rec in records.items():
        for item in rec["runs"] + rec["lifts"]:
            for p in _points(item):
                coarse.add((math.floor(p[1] / 0.05), math.floor(p[0] / 0.05)))
                near.setdefault((math.floor(p[1] / cell), math.floor(p[0] / cell)), []).append((p[0], p[1], sid))

    def candidate(item):
        for p in _points(item):
            cy, cx = math.floor(p[1] / 0.05), math.floor(p[0] / 0.05)
            if any((cy + dy, cx + dx) in coarse for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                return True
        return False

    orphans = []
    for kind, cols, filt, link in (("runs", RUN_COLUMNS, RUN_FILTER, "run"), ("lifts", LIFT_COLUMNS, LIFT_FILTER, "lift")):
        alias = "r" if kind == "runs" else "l"
        sql = (f"SELECT {cols} FROM {kind} {alias} WHERE {filt} AND NOT EXISTS ("
               f"SELECT 1 FROM {link}_ski_areas x JOIN app_areas a ON a.id = x.ski_area_id WHERE x.{link}_id = {alias}.id) "
               f"ORDER BY {alias}.id")
        for row in conn.execute(sql):
            item = dict(row)
            item["geom"] = simplify_geometry(item.pop("geometry_json"))
            if item["geom"] and candidate(item):
                orphans.append((kind, item))
    if not orphans:
        return {}

    # Group the orphans that touch each other (union-find on a grid).
    parent = list(range(len(orphans)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    lcell = ORPHAN_LINK_M / 111_320
    grid = {}
    for i, (_, item) in enumerate(orphans):
        for p in _points(item):
            grid.setdefault((math.floor(p[1] / lcell), math.floor(p[0] / lcell)), set()).add(i)
    for (cy, cx), members in grid.items():
        near_members = set(members)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                near_members |= grid.get((cy + dy, cx + dx), set())
        first = min(near_members)
        for j in near_members:
            parent[find(j)] = find(first)
    clusters = {}
    for i in range(len(orphans)):
        clusters.setdefault(find(i), []).append(i)

    def metres(a, b):
        k = math.cos(math.radians((a[1] + b[1]) / 2))
        return math.hypot((a[0] - b[0]) * 111_320 * k, (a[1] - b[1]) * 111_320)

    added = {}
    for members in clusters.values():
        best = None
        for i in members:
            for p in _points(orphans[i][1]):
                cy, cx = math.floor(p[1] / cell), math.floor(p[0] / cell)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        for q in near.get((cy + dy, cx + dx), ()):
                            d = metres(p, q)
                            if d <= ORPHAN_NEAR_M and (best is None or d < best[0]):
                                best = (d, q[2])
        if best is None:
            continue
        sid = best[1]
        rec = records[sid]
        runs = sorted((orphans[i][1] for i in members if orphans[i][0] == "runs"),
                      key=lambda r: (r.get("difficulty") or "", -(r.get("length_m") or 0), str(r["geom"][0][0])))
        lifts = sorted((orphans[i][1] for i in members if orphans[i][0] == "lifts"),
                       key=lambda l: (-(l.get("length_m") or 0), str(l["geom"][0][0])))
        rec["runs"] = rec["runs"] + runs
        rec["lifts"] = rec["lifts"] + lifts
        km = 0.0
        for r in runs:
            st = next((s for s in rec["run_stats"] if s.get("activity") == "downhill" and s.get("difficulty") == r.get("difficulty")), None)
            if st is None:
                st = {"ski_area_id": rec["id"], "activity": "downhill", "difficulty": r.get("difficulty"), "run_count": 0,
                      "length_km": 0.0, "snowmaking_length_km": 0.0, "snowfarming_length_km": 0.0}
                rec["run_stats"].append(st)
            st["run_count"] = (st.get("run_count") or 0) + 1
            st["length_km"] = (st.get("length_km") or 0) + (r.get("length_m") or 0) / 1000
            km += (r.get("length_m") or 0) / 1000
        for l in lifts:
            st = next((s for s in rec["lift_stats"] if s.get("lift_type") == l.get("lift_type")), None)
            if st is None:
                st = {"ski_area_id": rec["id"], "lift_type": l.get("lift_type"), "lift_count": 0, "length_km": 0.0}
                rec["lift_stats"].append(st)
            st["lift_count"] = (st.get("lift_count") or 0) + 1
            st["length_km"] = (st.get("length_km") or 0) + (l.get("length_m") or 0) / 1000
        a = added.setdefault(sid, [0, 0, 0.0])
        a[0] += len(runs); a[1] += len(lifts); a[2] += km
    return {k: tuple(v) for k, v in added.items()}


def find_moved(conn: sqlite3.Connection, old: dict) -> str | None:
    """OpenSkiMap sometimes gives a ski area a new id (it's derived from the
    OSM objects it's built from). Find it again: same country, and the same
    name within 5 km or any name within 1 km of where it was."""
    if old.get("latitude") is None:
        return None
    lat, lon = old["latitude"], old["longitude"]
    best = None
    for r in conn.execute("SELECT id, name, latitude, longitude FROM ski_areas WHERE country_code IS ? "
                          "AND latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?",
                          (old.get("country_code"), lat - 0.1, lat + 0.1, lon - 0.15, lon + 0.15)):
        if r["latitude"] is None:
            continue
        dy = (r["latitude"] - lat) * 111.2
        dx = (r["longitude"] - lon) * 111.2 * math.cos(math.radians(lat))
        d = math.hypot(dx, dy)
        same_name = (r["name"] or "").strip().lower() == (old.get("name") or "").strip().lower()
        if (same_name and d <= 5) or d <= 1:
            if best is None or d < best[0]:
                best = (d, r["id"])
    return best[1] if best else None


def downhill(record: dict) -> tuple[int, float]:
    runs = [r for r in record.get("runs") or [] if not r.get("uses") or "downhill" in r["uses"]]
    km = sum(s.get("length_km") or 0 for s in record.get("run_stats") or [] if s.get("activity") == "downhill")
    return len(runs), km


def same(a, b) -> bool:
    """Equal content, numbers compared with a tolerance: rebuilds differ in the
    last digits of computed lengths and centroids (1e-15), and SQLite hands
    REAL columns back as floats (0 vs 0.0) -- neither is worth a commit."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    return a == b


def _sort_key(x) -> str:
    def rounded(v):
        if isinstance(v, float):
            return round(v, 3)
        if isinstance(v, list):
            return [rounded(y) for y in v]
        if isinstance(v, dict):
            return {k: rounded(y) for k, y in v.items()}
        return v
    return json.dumps(rounded(x), sort_keys=True)


def same_record(old: dict, new: dict) -> bool:
    """same(), ignoring the order of runs/lifts/stats (equal-length runs can
    come in any order)."""
    if old.keys() != new.keys():
        return False
    for k in old:
        a, b = old[k], new[k]
        if k in ("runs", "lifts", "run_stats", "lift_stats") and isinstance(a, list) and isinstance(b, list):
            a, b = sorted(a, key=_sort_key), sorted(b, key=_sort_key)
        if not same(a, b):
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--docs", type=Path, default=REPO / "docs")
    ap.add_argument("--report", type=Path, help="write a Markdown summary here (e.g. $GITHUB_STEP_SUMMARY)")
    ap.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    paths = sorted((args.docs / "data").glob("*.json"))
    updated, unchanged, kept, moved_ids = [], 0, [], []
    writes = []
    olds, news, area_ids = {}, {}, set()
    for path in paths:
        old = json.loads(path.read_text(encoding="utf-8"))
        olds[path] = old
        area_ids.add(old["id"])
        new = station_record(conn, old["id"])
        name = old.get("name") or old["id"]
        if new is None:
            moved = find_moved(conn, old)
            if moved and os.path.exists(args.docs / "data" / f"{moved}.json"):
                moved = None  # that one is a station of its own in the app
            if moved:
                # Keep the app's id: slugs, favourites and stats are keyed on it.
                new = station_record(conn, moved)
                new["id"] = old["id"]
                for st in new["run_stats"] + new["lift_stats"]:
                    st["ski_area_id"] = old["id"]
                moved_ids.append((name, moved))
                area_ids.add(moved)
        if new is not None:
            news[old["id"]] = new
    absorbed = absorb_orphans(conn, news, area_ids)
    for path in paths:
        old = olds[path]
        new = news.get(old["id"])
        name = old.get("name") or old["id"]
        if new is None:
            kept.append((name, "not in the new OpenSkiMap data"))
            continue
        (old_runs, old_km), (new_runs, new_km) = downhill(old), downhill(new)
        if new_runs < old_runs * MIN_KEEP_RATIO or new_km < old_km * MIN_KEEP_RATIO:
            kept.append((name, f"downhill runs {old_runs} -> {new_runs}, km {old_km:.1f} -> {new_km:.1f}"))
            continue
        if not new.get("name"):
            new["name"] = old.get("name")
        for k, v in old.items():  # the services, and anything else not from OpenSkiMap
            new.setdefault(k, v)
        if same_record(old, new):
            unchanged += 1
            continue
        updated.append((name, old_runs, new_runs, old_km, new_km))
        writes.append((path, new))

    skipped_share = len(kept) / max(1, len(paths))
    lines = [f"## Station data refresh",
             f"- {len(paths)} stations: **{len(updated)} updated**, {unchanged} unchanged, {len(kept)} kept as they were"]
    abort = skipped_share > MAX_SKIPPED_SHARE
    if abort:
        lines.append(f"- **Nothing written**: {skipped_share:.0%} of the stations look wrong in the new data "
                     f"(limit {MAX_SKIPPED_SHARE:.0%}), so it's probably an OpenSkiMap problem.")
    if updated:
        lines += ["", "### Updated", "| Station | Runs | Downhill km |", "|---|---|---|"]
        lines += [f"| {n} | {a} → {b} | {c:.1f} → {d:.1f} |" for n, a, b, c, d in updated[:200]]
    if absorbed:
        names = {old["id"]: old.get("name") or old["id"] for old in olds.values()}
        lines += ["", "### Runs and lifts of no station, added to the one they touch", "| Station | Runs | Lifts | Downhill km |", "|---|---|---|---|"]
        lines += [f"| {names.get(i, i)} | +{a} | +{b} | +{c:.1f} |" for i, (a, b, c) in sorted(absorbed.items(), key=lambda x: -x[1][2])[:200]]
    if moved_ids:
        lines += ["", "### Found under a new OpenSkiMap id", "| Station | New id |", "|---|---|"]
        lines += [f"| {n} | {i} |" for n, i in moved_ids]
    if kept:
        lines += ["", "### Kept as they were", "| Station | Why |", "|---|---|"]
        lines += [f"| {n} | {why} |" for n, why in kept]
    report = "\n".join(lines) + "\n"
    print(report)
    if args.report:
        with open(args.report, "a", encoding="utf-8") as f:
            f.write(report)
    if abort:
        return 1
    if args.dry_run:
        return 0

    for path, record in writes:
        path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    if writes:
        update_catalogue(args.docs / "stations.js", {r["id"]: r for _, r in writes})
    return 0


def update_catalogue(path: Path, records: dict) -> None:
    """Refresh name/region/km/position of the updated stations in docs/stations.js
    (same rounding as when the catalogue was built); order and groups untouched."""
    lines = path.read_text(encoding="utf-8").split("\n")
    i = next(n for n, l in enumerate(lines) if l.startswith("var STATIONS = "))
    stations = json.loads(re.sub(r"^var STATIONS = |;\s*$", "", lines[i]))
    for s in stations:
        r = records.get(s["id"])
        if not r:
            continue
        _, km = downhill(r)
        s.update(name=r.get("name") or s["name"], region=r.get("region"), pisteKm=round(km, 1))
        if r.get("latitude") is not None:
            s.update(lat=round(r["latitude"], 4), lon=round(r["longitude"], 4))
    lines[i] = "var STATIONS = " + json.dumps(stations, ensure_ascii=False, separators=(",", ":")) + ";"
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
