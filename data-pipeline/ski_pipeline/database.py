"""SQLite schema creation and batch writers for the Ski Info database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


def insert_ski_areas(conn: sqlite3.Connection, rows: list[dict]) -> None:
    if not rows:
        return
    conn.executemany(
        """
        INSERT OR REPLACE INTO ski_areas (
            id, name, status, activities, run_convention, country_code,
            region, locality, latitude, longitude, min_elevation_m,
            max_elevation_m, wikidata_id, websites
        ) VALUES (
            :id, :name, :status, :activities, :run_convention, :country_code,
            :region, :locality, :latitude, :longitude, :min_elevation_m,
            :max_elevation_m, :wikidata_id, :websites
        )
        """,
        rows,
    )


def insert_ski_area_run_stats(conn: sqlite3.Connection, rows: list[dict]) -> None:
    if not rows:
        return
    conn.executemany(
        """
        INSERT OR REPLACE INTO ski_area_run_stats (
            ski_area_id, activity, difficulty, run_count, length_km,
            snowmaking_length_km, snowfarming_length_km
        ) VALUES (
            :ski_area_id, :activity, :difficulty, :run_count, :length_km,
            :snowmaking_length_km, :snowfarming_length_km
        )
        """,
        rows,
    )


def insert_ski_area_lift_stats(conn: sqlite3.Connection, rows: list[dict]) -> None:
    if not rows:
        return
    conn.executemany(
        """
        INSERT OR REPLACE INTO ski_area_lift_stats (
            ski_area_id, lift_type, lift_count, length_km
        ) VALUES (:ski_area_id, :lift_type, :lift_count, :length_km)
        """,
        rows,
    )


def insert_runs(conn: sqlite3.Connection, rows: list[dict]) -> None:
    if not rows:
        return
    conn.executemany(
        """
        INSERT OR REPLACE INTO runs (
            id, name, ref, status, difficulty, difficulty_convention, grooming,
            uses, lit, gladed, patrolled, snowmaking, snowfarming, oneway, tunnel,
            geometry_type, length_m, ascent_m, descent_m, vertical_m,
            min_elevation_m, max_elevation_m, avg_pitch_percent, max_pitch_percent,
            geometry_json
        ) VALUES (
            :id, :name, :ref, :status, :difficulty, :difficulty_convention, :grooming,
            :uses, :lit, :gladed, :patrolled, :snowmaking, :snowfarming, :oneway, :tunnel,
            :geometry_type, :length_m, :ascent_m, :descent_m, :vertical_m,
            :min_elevation_m, :max_elevation_m, :avg_pitch_percent, :max_pitch_percent,
            :geometry_json
        )
        """,
        rows,
    )


def insert_run_ski_areas(conn: sqlite3.Connection, rows: list[dict]) -> None:
    if not rows:
        return
    conn.executemany(
        "INSERT OR IGNORE INTO run_ski_areas (run_id, ski_area_id) VALUES (:run_id, :ski_area_id)",
        rows,
    )


def insert_lifts(conn: sqlite3.Connection, rows: list[dict]) -> None:
    if not rows:
        return
    conn.executemany(
        """
        INSERT OR REPLACE INTO lifts (
            id, name, ref, lift_type, status, access, occupancy, capacity,
            duration_s, detachable, bubble, heating, oneway, tunnel,
            length_m, vertical_m, geometry_json
        ) VALUES (
            :id, :name, :ref, :lift_type, :status, :access, :occupancy, :capacity,
            :duration_s, :detachable, :bubble, :heating, :oneway, :tunnel,
            :length_m, :vertical_m, :geometry_json
        )
        """,
        rows,
    )


def insert_lift_ski_areas(conn: sqlite3.Connection, rows: list[dict]) -> None:
    if not rows:
        return
    conn.executemany(
        "INSERT OR IGNORE INTO lift_ski_areas (lift_id, ski_area_id) VALUES (:lift_id, :ski_area_id)",
        rows,
    )
