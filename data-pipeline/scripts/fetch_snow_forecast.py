"""Fetch a 7-day snow forecast for every station into docs/snow.json.

Runs in the Pages deploy workflow (on every deploy and once a day on a
schedule), so the file is never committed. The home page ranks stations by
forecast snowfall from it ("Dónde va a nevar") and build_seo_pages.py adds the
forecast to each station page. Only daily snowfall is kept, to keep the file
small; the full forecast (temperatures, wind, snow depth...) is fetched live
by the pages themselves (docs/snow.js).

Source: Open-Meteo (https://open-meteo.com, CC BY 4.0), the same service the
app already uses for live weather. Up to BATCH stations go in one request
(Open-Meteo accepts comma-separated coordinate lists) and batches are spaced
out to stay well inside the free tier's per-minute limit. Each station is
forecast at its top elevation, where the snow that matters for skiing falls.

If the API cannot be reached the script exits 0 without writing anything:
the home page then hides the section and station pages skip the block, so a
flaky weather API never blocks a deploy.

Usage: python3 data-pipeline/scripts/fetch_snow_forecast.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT = DOCS / "snow.json"
BATCH = 100
PAUSE_S = 15  # 100 locations every 15 s = 400/min, under the 600/min limit
DAYS = 7
API = "https://api.open-meteo.com/v1/forecast"
DAILY = "snowfall_sum"


def load_stations() -> list[dict]:
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    line = next(l for l in html.splitlines() if l.startswith("  var STATIONS = "))
    stations = json.loads(re.sub(r"^  var STATIONS = |;\s*$", "", line))
    for s in stations:
        try:
            raw = json.loads((DOCS / "data" / f"{s['id']}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = {}
        s["lat"] = raw.get("latitude", s.get("lat"))
        s["lon"] = raw.get("longitude", s.get("lon"))
        s["top"] = raw.get("max_elevation_m")
    return [s for s in stations if s.get("lat") is not None and s.get("lon") is not None]


def fetch_batch(batch: list[dict]) -> list[dict]:
    params = {
        "latitude": ",".join(f"{s['lat']:.4f}" for s in batch),
        "longitude": ",".join(f"{s['lon']:.4f}" for s in batch),
        # "nan" = no downscaling, for the few stations without an elevation.
        "elevation": ",".join(str(round(s["top"])) if s.get("top") else "nan" for s in batch),
        "daily": DAILY,
        "forecast_days": DAYS,
        "timezone": "auto",
    }
    url = API + "?" + urllib.parse.urlencode(params, safe=",")
    last_err = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SkiInfo/1.0 (+https://skiinfoapp.com)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            return data if isinstance(data, list) else [data]
        except Exception as err:  # noqa: BLE001 -- network errors of every kind
            last_err = err
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"Open-Meteo batch failed: {last_err}")


def r1(v):
    return None if v is None else round(v, 1)


def main() -> None:
    stations = load_stations()
    out = {}
    for i in range(0, len(stations), BATCH):
        if i:
            time.sleep(PAUSE_S)
        batch = stations[i:i + BATCH]
        try:
            results = fetch_batch(batch)
        except RuntimeError as err:
            print(f"warning: {err}; snow.json not written", file=sys.stderr)
            return
        for s, res in zip(batch, results):
            d = res.get("daily") or {}
            if not d.get("time"):
                continue
            out[s["id"]] = {
                "d": d["time"][0],
                "sf": [r1(v) for v in d.get("snowfall_sum", [])],
                "el": round(s["top"]) if s.get("top") else None,
            }
    doc = {
        "updated": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "Open-Meteo.com (CC BY 4.0)",
        "stations": out,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"snow.json: {len(out)} stations")


if __name__ == "__main__":
    main()
