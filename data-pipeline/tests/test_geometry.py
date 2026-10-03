from __future__ import annotations

import math

from ski_pipeline import geometry


def test_haversine_distance_known_points():
    # Roughly 1 degree of latitude apart at the equator ~= 111.2 km.
    distance = geometry.haversine_distance_m([0.0, 0.0], [0.0, 1.0])
    assert math.isclose(distance, 111_195, rel_tol=0.01)


def test_line_metrics_flat_segment_has_no_pitch():
    coords = [[0.0, 0.0, 2000], [0.0, 0.01, 2000]]
    metrics = geometry.line_metrics(coords)

    assert metrics["ascent_m"] == 0.0
    assert metrics["descent_m"] == 0.0
    assert metrics["vertical_m"] == 0.0
    assert metrics["avg_pitch_percent"] == 0.0
    assert metrics["length_m"] > 0


def test_line_metrics_downhill_run():
    # ~1112 m horizontal, 100 m of descent -> ~9% average pitch.
    coords = [[0.0, 0.0, 2100], [0.0, 0.01, 2000]]
    metrics = geometry.line_metrics(coords)

    assert metrics["ascent_m"] == 0.0
    assert metrics["descent_m"] == 100.0
    assert metrics["min_elevation_m"] == 2000.0
    assert metrics["max_elevation_m"] == 2100.0
    assert metrics["vertical_m"] == 100.0
    assert metrics["avg_pitch_percent"] == metrics["max_pitch_percent"]
    assert 8.0 < metrics["avg_pitch_percent"] < 10.0


def test_line_metrics_without_elevation_only_computes_length():
    coords = [[0.0, 0.0], [0.0, 0.01]]
    metrics = geometry.line_metrics(coords)

    assert metrics["length_m"] > 0
    assert metrics["ascent_m"] is None
    assert metrics["vertical_m"] is None
    assert metrics["avg_pitch_percent"] is None


def test_line_metrics_needs_at_least_two_points():
    assert geometry.line_metrics([[0.0, 0.0, 2000]]) == geometry.empty_metrics()
    assert geometry.line_metrics([]) == geometry.empty_metrics()


def test_geometry_metrics_multilinestring_sums_parts():
    geom = {
        "type": "MultiLineString",
        "coordinates": [
            [[0.0, 0.0, 2000], [0.0, 0.01, 1950]],
            [[0.0, 0.01, 1950], [0.0, 0.02, 1900]],
        ],
    }
    metrics = geometry.geometry_metrics(geom)

    assert metrics["descent_m"] == 100.0
    assert metrics["min_elevation_m"] == 1900.0
    assert metrics["max_elevation_m"] == 2000.0
    assert metrics["vertical_m"] == 100.0
    assert metrics["length_m"] > 0


def test_geometry_metrics_polygon_has_no_linear_metrics():
    geom = {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]}
    assert geometry.geometry_metrics(geom) == geometry.empty_metrics()


def test_geometry_metrics_handles_missing_geometry():
    assert geometry.geometry_metrics(None) == geometry.empty_metrics()
