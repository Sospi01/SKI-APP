"""Length, ascent/descent and pitch metrics derived from run/lift geometries.

OpenSkiMap embeds elevation as a third coordinate (lon, lat, elevation) on
LineString geometries, which is what lets us compute real slope pitch instead
of relying only on the coarse "difficulty" tag. This mirrors the
AscentDescentData/PitchData that openskidata-format computes upstream
(see ElevationProfile.ts), recomputed here directly from those coordinates.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

EARTH_RADIUS_M = 6_371_000.0

Coordinate = Sequence[float]


def haversine_distance_m(a: Coordinate, b: Coordinate) -> float:
    """Great-circle distance in meters between two [lon, lat, ...] coordinates."""
    lon1, lat1 = math.radians(a[0]), math.radians(a[1])
    lon2, lat2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def empty_metrics() -> dict[str, Any]:
    return {
        "length_m": None,
        "ascent_m": None,
        "descent_m": None,
        "vertical_m": None,
        "min_elevation_m": None,
        "max_elevation_m": None,
        "avg_pitch_percent": None,
        "max_pitch_percent": None,
    }


def line_metrics(coordinates: list[Coordinate]) -> dict[str, Any]:
    """Compute length/elevation/pitch metrics for a single LineString's coordinates."""
    if len(coordinates) < 2:
        return empty_metrics()

    has_elevation = len(coordinates[0]) >= 3

    length_m = 0.0
    ascent_m = 0.0
    descent_m = 0.0
    elevations: list[float] = []
    max_pitch_percent: float | None = None

    for prev, curr in zip(coordinates, coordinates[1:]):
        segment_m = haversine_distance_m(prev, curr)
        length_m += segment_m

        if has_elevation:
            elevations.append(prev[2])
            delta = curr[2] - prev[2]
            if delta > 0:
                ascent_m += delta
            else:
                descent_m += -delta
            if segment_m > 0:
                pitch = abs(delta) / segment_m * 100
                if max_pitch_percent is None or pitch > max_pitch_percent:
                    max_pitch_percent = pitch

    if has_elevation:
        elevations.append(coordinates[-1][2])

    min_elevation_m = min(elevations) if elevations else None
    max_elevation_m = max(elevations) if elevations else None
    vertical_m = (max_elevation_m - min_elevation_m) if elevations else None
    avg_pitch_percent = (
        vertical_m / length_m * 100 if vertical_m is not None and length_m > 0 else None
    )

    return {
        "length_m": round(length_m, 1),
        "ascent_m": round(ascent_m, 1) if has_elevation else None,
        "descent_m": round(descent_m, 1) if has_elevation else None,
        "vertical_m": round(vertical_m, 1) if vertical_m is not None else None,
        "min_elevation_m": round(min_elevation_m, 1) if min_elevation_m is not None else None,
        "max_elevation_m": round(max_elevation_m, 1) if max_elevation_m is not None else None,
        "avg_pitch_percent": round(avg_pitch_percent, 1) if avg_pitch_percent is not None else None,
        "max_pitch_percent": round(max_pitch_percent, 1) if max_pitch_percent is not None else None,
    }


def _sum_part_metrics(parts: list[dict[str, Any]]) -> dict[str, Any]:
    lengths = [p["length_m"] for p in parts if p["length_m"] is not None]
    ascents = [p["ascent_m"] for p in parts if p["ascent_m"] is not None]
    descents = [p["descent_m"] for p in parts if p["descent_m"] is not None]
    elev_mins = [p["min_elevation_m"] for p in parts if p["min_elevation_m"] is not None]
    elev_maxs = [p["max_elevation_m"] for p in parts if p["max_elevation_m"] is not None]
    max_pitches = [p["max_pitch_percent"] for p in parts if p["max_pitch_percent"] is not None]

    length_m = sum(lengths) if lengths else None
    vertical_m = (max(elev_maxs) - min(elev_mins)) if elev_mins and elev_maxs else None
    avg_pitch_percent = (
        vertical_m / length_m * 100 if vertical_m is not None and length_m else None
    )

    return {
        "length_m": round(length_m, 1) if length_m is not None else None,
        "ascent_m": round(sum(ascents), 1) if ascents else None,
        "descent_m": round(sum(descents), 1) if descents else None,
        "vertical_m": round(vertical_m, 1) if vertical_m is not None else None,
        "min_elevation_m": round(min(elev_mins), 1) if elev_mins else None,
        "max_elevation_m": round(max(elev_maxs), 1) if elev_maxs else None,
        "avg_pitch_percent": round(avg_pitch_percent, 1) if avg_pitch_percent is not None else None,
        "max_pitch_percent": round(max(max_pitches), 1) if max_pitches else None,
    }


def geometry_metrics(geometry: dict[str, Any] | None) -> dict[str, Any]:
    """Compute length/elevation metrics for a Run/Lift geometry.

    Only LineString and MultiLineString carry linear metrics; Polygon
    geometries (e.g. snow parks) aren't linear features so metrics are None.
    """
    if not geometry:
        return empty_metrics()

    gtype = geometry.get("type")
    if gtype == "LineString":
        return line_metrics(geometry["coordinates"])
    if gtype == "MultiLineString":
        parts = [line_metrics(part) for part in geometry["coordinates"]]
        return _sum_part_metrics(parts) if parts else empty_metrics()
    return empty_metrics()
