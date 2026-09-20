from __future__ import annotations

from pathlib import Path

from ski_pipeline import transform

FIXTURES = Path(__file__).parent / "fixtures"


def test_iter_features_streams_all_features():
    features = list(transform.iter_features(FIXTURES / "ski_areas.sample.geojson"))
    assert len(features) == 2
    assert {f["properties"]["id"] for f in features} == {"skiarea-1", "skiarea-2"}


def test_transform_ski_area_flattens_location_and_stats():
    features = list(transform.iter_features(FIXTURES / "ski_areas.sample.geojson"))
    row = transform.transform_ski_area(features[0])

    assert row["id"] == "skiarea-1"
    assert row["activities"] == "downhill"
    assert row["country_code"] == "AT"
    assert row["region"] == "Tyrol"
    assert row["locality"] == "Sample Village"
    assert row["longitude"] == 10.9646
    assert row["latitude"] == 46.9658
    assert row["min_elevation_m"] == 1350
    assert row["max_elevation_m"] == 3340
    assert row["wikidata_id"] == "Q123456"
    assert row["websites"] == '["https://example.com"]'


def test_transform_ski_area_handles_missing_statistics_and_places():
    features = list(transform.iter_features(FIXTURES / "ski_areas.sample.geojson"))
    row = transform.transform_ski_area(features[1])

    assert row["id"] == "skiarea-2"
    assert row["country_code"] is None
    assert row["min_elevation_m"] is None
    assert row["websites"] == "[]"


def test_transform_ski_area_run_stats_flattens_by_activity_and_difficulty():
    features = list(transform.iter_features(FIXTURES / "ski_areas.sample.geojson"))
    rows = transform.transform_ski_area_run_stats(features[0])

    by_difficulty = {row["difficulty"]: row for row in rows}
    assert by_difficulty["easy"]["length_km"] == 15.2
    assert by_difficulty["easy"]["snowmaking_length_km"] == 12.0
    assert by_difficulty["advanced"]["snowmaking_length_km"] is None
    assert all(row["activity"] == "downhill" for row in rows)
    assert all(row["ski_area_id"] == "skiarea-1" for row in rows)


def test_transform_ski_area_lift_stats():
    features = list(transform.iter_features(FIXTURES / "ski_areas.sample.geojson"))
    rows = transform.transform_ski_area_lift_stats(features[0])

    by_type = {row["lift_type"]: row for row in rows}
    assert by_type["gondola"]["lift_count"] == 3
    assert by_type["chair_lift"]["length_km"] == 25.0


def test_transform_run_computes_metrics_and_flags():
    features = list(transform.iter_features(FIXTURES / "runs.sample.geojson"))
    run_by_id = {f["properties"]["id"]: f for f in features}

    row, ski_area_ids = transform.transform_run(run_by_id["run-1"])

    assert row["id"] == "run-1"
    assert row["difficulty"] == "easy"
    assert row["grooming"] == "classic"
    assert row["uses"] == "downhill"
    assert row["lit"] == 0
    assert row["patrolled"] == 1
    assert row["snowmaking"] == 1
    assert row["length_m"] > 0
    assert row["descent_m"] == 100.0
    assert ski_area_ids == ["skiarea-1"]


def test_transform_run_polygon_geometry_has_no_linear_metrics():
    features = list(transform.iter_features(FIXTURES / "runs.sample.geojson"))
    run_by_id = {f["properties"]["id"]: f for f in features}

    row, ski_area_ids = transform.transform_run(run_by_id["run-3"])

    assert row["geometry_type"] == "Polygon"
    assert row["length_m"] is None
    assert ski_area_ids == []


def test_transform_lift_computes_metrics_and_flags():
    features = list(transform.iter_features(FIXTURES / "lifts.sample.geojson"))
    lift_by_id = {f["properties"]["id"]: f for f in features}

    row, ski_area_ids = transform.transform_lift(lift_by_id["lift-1"])

    assert row["id"] == "lift-1"
    assert row["lift_type"] == "gondola"
    assert row["capacity"] == 2400
    assert row["occupancy"] == 8
    assert row["detachable"] == 1
    assert row["bubble"] == 1
    assert row["vertical_m"] == 500.0
    assert ski_area_ids == ["skiarea-1"]


def test_transform_lift_private_access():
    features = list(transform.iter_features(FIXTURES / "lifts.sample.geojson"))
    lift_by_id = {f["properties"]["id"]: f for f in features}

    row, _ = transform.transform_lift(lift_by_id["lift-2"])

    assert row["access"] == "private"
    assert row["detachable"] == 0
