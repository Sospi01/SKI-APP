"""Constants for the OpenSkiMap data pipeline: source URLs and default paths."""

from __future__ import annotations

from pathlib import Path

OPENSKIMAP_BASE_URL = "https://tiles.openskimap.org/geojson"

SKI_AREAS_URL = f"{OPENSKIMAP_BASE_URL}/ski_areas.geojson"
RUNS_URL = f"{OPENSKIMAP_BASE_URL}/runs.geojson"
LIFTS_URL = f"{OPENSKIMAP_BASE_URL}/lifts.geojson"

DEFAULT_DATA_DIR = Path("data")
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "ski_info.db"

USER_AGENT = "SkiInfoApp-DataPipeline/0.1 (+https://github.com/sospi01/ski-app)"
