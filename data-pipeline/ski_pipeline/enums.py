"""Value sets from OpenSkiMap's data format (`openskidata-format`).

Mirrors https://github.com/russellporter/openskidata-format for reference and
for ordering difficulties in the app's UI. Values are passed through as plain
strings elsewhere in the pipeline rather than validated against these lists,
since OSM tagging evolves and new values shouldn't break ingestion.
"""

from __future__ import annotations

# Ordered from easiest to hardest, matching the European difficulty progression.
RUN_DIFFICULTY_ORDER = [
    "novice",
    "easy",
    "intermediate",
    "advanced",
    "expert",
    "freeride",
    "extreme",
]

RUN_GROOMING_VALUES = [
    "classic",
    "mogul",
    "classic+skating",
    "skating",
    "scooter",
    "backcountry",
]

RUN_USE_VALUES = [
    "downhill",
    "nordic",
    "skitour",
    "sled",
    "hike",
    "sleigh",
    "ice_skate",
    "snow_park",
    "playground",
    "connection",
    "fatbike",
]

LIFT_TYPE_VALUES = [
    "cable_car",
    "gondola",
    "chair_lift",
    "mixed_lift",
    "drag_lift",
    "t-bar",
    "j-bar",
    "platter",
    "rope_tow",
    "magic_carpet",
    "funicular",
    "railway",
]

SKI_AREA_ACTIVITY_VALUES = ["downhill", "nordic"]
