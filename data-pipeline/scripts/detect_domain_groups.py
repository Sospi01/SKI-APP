#!/usr/bin/env python3
"""Detect ski areas that are physically connected despite being separate
OpenStreetMap/OpenSkiMap entries.

There's no reliable "part of domain X" tag on ski areas to read this from,
so instead this looks at the actual mapped geometry: it loads every run and
lift belonging to each station (from docs/data/<id>.json) and checks whether
any two stations have points within DISTANCE_THRESHOLD_M of each other. Two
stations that close are almost certainly reachable from one another by piste
or lift, i.e. part of the same skiable domain even if OSM tags them
separately (this is exactly how Vía Láctea's five components -- Sestriere,
Sauze D'Oulx, Sansicario, Montgenèvre, Claviere -- get grouped automatically).

It will NOT catch a connection whose linking piste/lift isn't mapped in
either station's geometry yet (Formigal-Panticosa is the known example: the
two are ~8km apart in the current OSM data despite being sold as one lift
pass in real life). That's a genuine data gap, not a bug in this script --
raise DISTANCE_THRESHOLD_M to compensate and you'll start pulling in
unrelated resorts across a valley instead.

Usage:
    python3 scripts/detect_domain_groups.py [--data-dir DIR] [--threshold-m N]

Prints the human-readable groups to stderr and the JS array literal (ready
to paste into docs/index.html's STATION_GROUPS constant) to stdout.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import sys
from pathlib import Path

DEFAULT_THRESHOLD_M = 500


def load_station(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    points: list[tuple[float, float]] = []
    for collection in ("runs", "lifts"):
        for item in d.get(collection, []):
            geom = item.get("geom")
            if not geom:
                continue
            for part in geom:
                points.extend((c[0], c[1]) for c in part)
    return {"id": d["id"], "name": d["name"], "points": points}


def bbox_of(points, pad_lat, pad_lon):
    if not points:
        return None
    lons = [p[0] for p in points]
    lats = [p[1] for p in points]
    return (min(lons) - pad_lon, max(lons) + pad_lon, min(lats) - pad_lat, max(lats) + pad_lat)


def bbox_overlap(a, b) -> bool:
    if a is None or b is None:
        return False
    return not (a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2])


def min_dist_m(pts_a, pts_b, cutoff_m: float) -> float | None:
    """Grid-bucket pts_b so this stays roughly linear instead of O(len(a)*len(b))."""
    cell = cutoff_m / 111_000.0
    buckets: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for lon, lat in pts_b:
        buckets.setdefault((int(lon / cell), int(lat / cell)), []).append((lon, lat))

    best = None
    for lon, lat in pts_a:
        cx, cy = int(lon / cell), int(lat / cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for lon2, lat2 in buckets.get((cx + dx, cy + dy), []):
                    dlat = (lat2 - lat) * 111_000
                    dlon = (lon2 - lon) * 111_000 * math.cos(math.radians((lat + lat2) / 2))
                    d = math.hypot(dlat, dlon)
                    if best is None or d < best:
                        best = d
                        if best < 1:
                            return best
    return best


class UnionFind:
    def __init__(self, ids):
        self.parent = {i: i for i in ids}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", default="../docs/data", help="Directory of per-station JSON files")
    parser.add_argument("--threshold-m", type=float, default=DEFAULT_THRESHOLD_M)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    paths = sorted(glob.glob(str(data_dir / "*.json")))
    if not paths:
        sys.exit(f"No station JSON files found under {data_dir}")

    stations = [load_station(Path(p)) for p in paths]
    pad_lat = args.threshold_m / 111_000
    pad_lon = args.threshold_m / (111_000 * math.cos(math.radians(45)))
    for s in stations:
        s["bbox"] = bbox_of(s["points"], pad_lat, pad_lon)

    uf = UnionFind(s["id"] for s in stations)
    n = len(stations)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = stations[i], stations[j]
            if not bbox_overlap(a["bbox"], b["bbox"]):
                continue
            d = min_dist_m(a["points"], b["points"], args.threshold_m)
            if d is not None and d <= args.threshold_m:
                uf.union(a["id"], b["id"])

    name_by_id = {s["id"]: s["name"] for s in stations}
    grouped: dict[str, list[str]] = {}
    for s in stations:
        grouped.setdefault(uf.find(s["id"]), []).append(s["id"])
    groups = [sorted(ids) for ids in grouped.values() if len(ids) > 1]

    print(f"{len(groups)} groups covering {sum(len(g) for g in groups)} of {n} stations "
          f"(threshold {args.threshold_m:.0f}m)", file=sys.stderr)
    for ids in groups:
        print("  " + " + ".join(name_by_id[i] for i in ids), file=sys.stderr)

    print(json.dumps(groups, separators=(",", ":")))


if __name__ == "__main__":
    main()
