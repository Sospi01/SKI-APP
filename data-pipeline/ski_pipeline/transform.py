"""Turns OpenSkiMap GeoJSON features into flat rows ready for SQLite.

Field names below follow the properties documented in openskidata-format
(https://github.com/russellporter/openskidata-format): SkiArea.ts, Run.ts and
Lift.ts. Unknown/missing values are passed through as None rather than
rejected, since OSM tagging is incomplete by nature.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import ijson

from . import geometry


def iter_features(path: Path) -> Iterator[dict[str, Any]]:
    """Stream GeoJSON Feature objects one at a time without loading the whole file."""
    with path.open("rb") as f:
        yield from ijson.items(f, "features.item", use_float=True)


def _bool_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return 1 if value else 0


def _anchor_point(geom: dict[str, Any] | None) -> tuple[float | None, float | None]:
    """Pick a representative [lon, lat] for a ski area, whatever its geometry type."""
    if not geom:
        return None, None
    coords = geom.get("coordinates")
    if not coords:
        return None, None
    if geom.get("type") == "Point":
        return coords[0], coords[1]
    # Polygon/MultiPolygon: descend into the first ring's first point.
    ring = coords
    while isinstance(ring, list) and ring and isinstance(ring[0], list):
        ring = ring[0]
    if isinstance(ring, list) and len(ring) >= 2:
        return ring[0], ring[1]
    return None, None


def transform_ski_area(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature["properties"]
    lon, lat = _anchor_point(feature.get("geometry"))

    places = props.get("places") or []
    place = places[0] if places else {}
    localized = (place.get("localized") or {}).get("en", {})

    stats = props.get("statistics") or {}

    return {
        "id": props["id"],
        "name": props.get("name"),
        "status": props.get("status"),
        "activities": ",".join(sorted(props.get("activities") or [])),
        "run_convention": props.get("runConvention"),
        "country_code": place.get("iso3166_1Alpha2"),
        "region": localized.get("region"),
        "locality": localized.get("locality"),
        "latitude": lat,
        "longitude": lon,
        "min_elevation_m": stats.get("minElevation"),
        "max_elevation_m": stats.get("maxElevation"),
        "wikidata_id": props.get("wikidataID"),
        "websites": json.dumps(props.get("websites") or []),
    }


def transform_ski_area_run_stats(feature: dict[str, Any]) -> list[dict[str, Any]]:
    props = feature["properties"]
    ski_area_id = props["id"]
    run_stats = ((props.get("statistics") or {}).get("runs") or {}).get("byActivity") or {}

    rows = []
    for activity, by_difficulty in run_stats.items():
        for difficulty, values in (by_difficulty.get("byDifficulty") or {}).items():
            rows.append(
                {
                    "ski_area_id": ski_area_id,
                    "activity": activity,
                    "difficulty": difficulty,
                    "run_count": values.get("count", 0),
                    "length_km": values.get("lengthInKm", 0.0),
                    "snowmaking_length_km": values.get("snowmakingLengthInKm"),
                    "snowfarming_length_km": values.get("snowfarmingLengthInKm"),
                }
            )
    return rows


def transform_ski_area_lift_stats(feature: dict[str, Any]) -> list[dict[str, Any]]:
    props = feature["properties"]
    ski_area_id = props["id"]
    lift_stats = ((props.get("statistics") or {}).get("lifts") or {}).get("byType") or {}

    return [
        {
            "ski_area_id": ski_area_id,
            "lift_type": lift_type,
            "lift_count": values.get("count", 0),
            "length_km": values.get("lengthInKm", 0.0),
        }
        for lift_type, values in lift_stats.items()
    ]


def _ski_area_ids(props: dict[str, Any]) -> list[str]:
    return [sa["properties"]["id"] for sa in props.get("skiAreas") or []]


def transform_run(feature: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    props = feature["properties"]
    geom = feature.get("geometry")
    metrics = geometry.geometry_metrics(geom)

    row = {
        "id": props["id"],
        "name": props.get("name"),
        "ref": props.get("ref"),
        "status": props.get("status"),
        "difficulty": props.get("difficulty"),
        "difficulty_convention": props.get("difficultyConvention"),
        "grooming": props.get("grooming"),
        "uses": ",".join(props.get("uses") or []),
        "lit": _bool_or_none(props.get("lit")),
        "gladed": _bool_or_none(props.get("gladed")),
        "patrolled": _bool_or_none(props.get("patrolled")),
        "snowmaking": _bool_or_none(props.get("snowmaking")),
        "snowfarming": _bool_or_none(props.get("snowfarming")),
        "oneway": _bool_or_none(props.get("oneway")),
        "tunnel": _bool_or_none(props.get("tunnel")),
        "geometry_type": geom.get("type") if geom else None,
        "geometry_json": json.dumps(geom) if geom else None,
        **metrics,
    }
    return row, _ski_area_ids(props)


def transform_lift(feature: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    props = feature["properties"]
    geom = feature.get("geometry")
    metrics = geometry.geometry_metrics(geom)

    row = {
        "id": props["id"],
        "name": props.get("name"),
        "ref": props.get("ref"),
        "lift_type": props.get("liftType"),
        "status": props.get("status"),
        "access": props.get("access"),
        "occupancy": props.get("occupancy"),
        "capacity": props.get("capacity"),
        "duration_s": props.get("duration"),
        "detachable": _bool_or_none(props.get("detachable")),
        "bubble": _bool_or_none(props.get("bubble")),
        "heating": _bool_or_none(props.get("heating")),
        "oneway": _bool_or_none(props.get("oneway")),
        "tunnel": _bool_or_none(props.get("tunnel")),
        "length_m": metrics["length_m"],
        "vertical_m": metrics["vertical_m"],
        "geometry_json": json.dumps(geom) if geom else None,
    }
    return row, _ski_area_ids(props)
