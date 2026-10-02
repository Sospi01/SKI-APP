"""Add ski areas that aren't in the app yet, from an OpenSkiMap database.

The weekly refresh (refresh_stations.py) never adds stations; this is the
reviewed, on-demand step that does, run by .github/workflows/add-stations.yml
(OpenSkiMap can only be downloaded there). For one country it picks the ski
areas the original catalogue would have taken (downhill, operating, with runs
and lifts) with at least --min-km of downhill runs, skipping the ones already
in the app and any within 1.5 km of a station it already has (the same area
under another OpenSkiMap id, or a part of a domain it already shows). Each new
one gets its data file (same shape as the others, with no services yet) and an
entry in docs/stations.js; slugs are pinned afterwards by
build_seo_pages.py --write-slugs.

With --dry-run it only reports what it would add.

Usage: python3 data-pipeline/scripts/add_stations.py --db data-pipeline/data/ski_info.db --country US --min-km 3
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refresh_stations import REPO, downhill, station_record  # noqa: E402

NEAR_KM = 1.5


def candidates(conn: sqlite3.Connection, country: str, min_km: float) -> list[dict]:
    """Same selection as the catalogue's original fetch (fetch-stations.yml)."""
    return [dict(r) for r in conn.execute(
        """
        SELECT sa.id, sa.name, sa.region, sa.latitude, sa.longitude,
               COALESCE((SELECT SUM(length_km) FROM ski_area_run_stats
                         WHERE ski_area_id = sa.id AND activity = 'downhill'), 0) AS km
        FROM ski_areas sa
        WHERE sa.country_code = ? AND sa.activities LIKE '%downhill%'
          AND sa.status = 'operating'
          AND (SELECT COUNT(*) FROM run_ski_areas WHERE ski_area_id = sa.id) > 0
          AND (SELECT COUNT(*) FROM lift_ski_areas WHERE ski_area_id = sa.id) > 0
          AND COALESCE((SELECT SUM(length_km) FROM ski_area_run_stats
                        WHERE ski_area_id = sa.id AND activity = 'downhill'), 0) >= ?
        ORDER BY km DESC, sa.id
        """, (country, min_km))]


def km_between(a: tuple, b: tuple) -> float:
    dy = (a[0] - b[0]) * 111.2
    dx = (a[1] - b[1]) * 111.2 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dx, dy)


def read_catalogue(path: Path) -> tuple[list[str], int, list[dict]]:
    lines = path.read_text(encoding="utf-8").split("\n")
    i = next(n for n, l in enumerate(lines) if l.startswith("var STATIONS = "))
    return lines, i, json.loads(re.sub(r"^var STATIONS = |;\s*$", "", lines[i]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--docs", type=Path, default=REPO / "docs")
    ap.add_argument("--country", required=True, help="ISO code, e.g. US")
    ap.add_argument("--min-km", type=float, default=3.0, help="minimum km of downhill runs")
    ap.add_argument("--max-new", type=int, default=150, help="add at most this many (largest first)")
    ap.add_argument("--dry-run", action="store_true", help="only report what would be added")
    ap.add_argument("--report", type=Path, help="append a Markdown summary here (e.g. $GITHUB_STEP_SUMMARY)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cat_path = args.docs / "stations.js"
    lines, line_no, stations = read_catalogue(cat_path)
    known = {s["id"] for s in stations}
    known |= {p.stem for p in (args.docs / "data").glob("*.json")}
    known_pts = [(s["lat"], s["lon"], s["name"]) for s in stations if s.get("lat") is not None]

    added, near = [], []
    for c in candidates(conn, args.country, args.min_km):
        if c["id"] in known or c["latitude"] is None:
            continue
        pt = (c["latitude"], c["longitude"])
        close = next((n for la, lo, n in known_pts if km_between(pt, (la, lo)) <= NEAR_KM), None)
        if close:
            near.append((c["name"] or c["id"], c["km"], close))
            continue
        if len(added) >= args.max_new:
            break
        record = station_record(conn, c["id"])
        if record is None or not record.get("name"):
            continue
        runs, km = downhill(record)
        if not runs:
            continue
        record["services"] = []
        added.append(record)
        known_pts.append((pt[0], pt[1], record["name"]))

    lines_md = [f"## Add stations: {args.country}, at least {args.min_km:g} km" + (" (dry run)" if args.dry_run else ""),
                f"- **{len(added)} new** · {len(near)} skipped as too close to a station already in the app"]
    if added:
        lines_md += ["", "### New", "| Station | Region | Downhill km | Runs | Lifts |", "|---|---|---|---|---|"]
        lines_md += [f"| {r['name']} | {r.get('region') or ''} | {downhill(r)[1]:.1f} | {downhill(r)[0]} | {len(r.get('lifts') or [])} |"
                     for r in added]
    if near:
        lines_md += ["", "### Skipped (within 1.5 km of a station already in the app)", "| Candidate | km | Near |", "|---|---|---|"]
        lines_md += [f"| {n} | {k:.1f} | {c} |" for n, k, c in near[:100]]
    report = "\n".join(lines_md) + "\n"
    print(report)
    if args.report:
        with open(args.report, "a", encoding="utf-8") as f:
            f.write(report)
    if args.dry_run or not added:
        return 0

    for r in added:
        (args.docs / "data" / f"{r['id']}.json").write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
        stations.append({"id": r["id"], "name": r["name"], "region": r.get("region"), "pisteKm": round(downhill(r)[1], 1),
                         "country": r.get("country_code") or args.country,
                         "lat": round(r["latitude"], 4), "lon": round(r["longitude"], 4)})
    lines[line_no] = "var STATIONS = " + json.dumps(stations, ensure_ascii=False, separators=(",", ":")) + ";"
    cat_path.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
