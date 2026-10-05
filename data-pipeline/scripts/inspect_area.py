"""List every run and lift OpenSkiMap has inside a box, with its ski areas,
status and uses, and whether a station of the app takes it -- to find out
why some pistes don't show up. Read-only.

Usage: python3 data-pipeline/scripts/inspect_area.py --db data-pipeline/data/ski_info.db \
           --bbox 6.74,44.92,6.84,44.98
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--bbox", required=True, help="lon_min,lat_min,lon_max,lat_max")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    x0, y0, x1, y1 = (float(v) for v in args.bbox.split(","))
    app = {p.stem for p in (REPO / "docs" / "data").glob("*.json")}
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    names = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM ski_areas")}
    out = [f"## Runs and lifts in {args.bbox}", ""]
    for kind, link, cols in (("runs", "run", "name, ref, difficulty, status, uses, length_m"),
                             ("lifts", "lift", "name, ref, lift_type AS difficulty, status, NULL AS uses, length_m")):
        out += [f"### {kind}", "| Name | Ref | Kind | Status | Uses | km | Ski areas |", "|---|---|---|---|---|---|---|"]
        n = 0
        for r in conn.execute(f"SELECT id, {cols}, geometry_json FROM {kind}"):
            g = json.loads(r["geometry_json"] or "null") or {}
            c = g.get("coordinates") or []
            pts = c if g.get("type") == "LineString" else [p for part in c for p in part] if g.get("type") in ("MultiLineString", "Polygon") else []
            if not any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in pts):
                continue
            areas = [a[0] for a in conn.execute(f"SELECT ski_area_id FROM {link}_ski_areas WHERE {link}_id = ?", (r["id"],))]
            label = ", ".join(("✅ " if a in app else "") + (names.get(a) or a) for a in areas) or "(none)"
            out.append(f"| {r['name'] or ''} | {r['ref'] or ''} | {r['difficulty'] or ''} | {r['status'] or ''} | {r['uses'] or ''} | "
                       f"{(r['length_m'] or 0) / 1000:.2f} | {label} |")
            n += 1
        out += [f"", f"{n} {kind}", ""]
    report = "\n".join(out) + "\n"
    print(report)
    if args.report:
        with open(args.report, "a", encoding="utf-8") as f:
            f.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
