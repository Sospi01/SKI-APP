"""Downloads OpenSkiMap's GeoJSON source files with retries and backoff."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

from . import config

logger = logging.getLogger(__name__)

SOURCES = {
    "ski_areas": config.SKI_AREAS_URL,
    "runs": config.RUNS_URL,
    "lifts": config.LIFTS_URL,
}


def download_file(
    url: str,
    dest: Path,
    *,
    timeout: int = 60,
    retries: int = 4,
    chunk_size: int = 1 << 20,
) -> Path:
    """Stream `url` to `dest`, retrying with exponential backoff on failure.

    Writes to a `.part` file first and only replaces `dest` on success, so a
    failed attempt never leaves a truncated file where the pipeline expects
    a complete one.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_dest = dest.with_suffix(dest.suffix + ".part")

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with requests.get(
                url,
                stream=True,
                timeout=timeout,
                headers={"User-Agent": config.USER_AGENT},
            ) as response:
                response.raise_for_status()
                with tmp_dest.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
            tmp_dest.replace(dest)
            logger.info("Downloaded %s -> %s", url, dest)
            return dest
        except requests.RequestException as exc:
            last_error = exc
            tmp_dest.unlink(missing_ok=True)
            if attempt == retries:
                break
            wait = 2**attempt
            logger.warning(
                "Download attempt %d/%d for %s failed: %s. Retrying in %ds",
                attempt,
                retries,
                url,
                exc,
                wait,
            )
            time.sleep(wait)

    raise RuntimeError(f"Failed to download {url} after {retries} attempts") from last_error


def download_all(data_dir: Path, *, force: bool = False) -> dict[str, Path]:
    """Download every source into `data_dir`, skipping files that already exist."""
    paths = {}
    for name, url in SOURCES.items():
        dest = data_dir / f"{name}.geojson"
        if dest.exists() and not force:
            logger.info(
                "Skipping %s, already downloaded at %s (use --force-download to refresh)",
                name,
                dest,
            )
        else:
            download_file(url, dest)
        paths[name] = dest
    return paths
