from __future__ import annotations

from unittest.mock import patch

import pytest
import requests

from ski_pipeline import download


class FakeResponse:
    def __init__(self, chunks: list[bytes], status_error: Exception | None = None):
        self._chunks = chunks
        self._status_error = status_error

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def iter_content(self, chunk_size):
        yield from self._chunks


def test_download_file_writes_content(tmp_path):
    dest = tmp_path / "ski_areas.geojson"
    fake_response = FakeResponse([b'{"type": ', b'"FeatureCollection"}'])

    with patch.object(download.requests, "get", return_value=fake_response) as mock_get:
        result = download.download_file("https://example.com/ski_areas.geojson", dest)

    assert result == dest
    assert dest.read_bytes() == b'{"type": "FeatureCollection"}'
    assert not dest.with_suffix(dest.suffix + ".part").exists()
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs["headers"]["User-Agent"] == download.config.USER_AGENT


def test_download_file_retries_then_succeeds(tmp_path):
    dest = tmp_path / "runs.geojson"
    responses = [
        FakeResponse([], status_error=requests.ConnectionError("boom")),
        FakeResponse([b"{}"]),
    ]

    with patch.object(download.requests, "get", side_effect=responses):
        with patch.object(download.time, "sleep") as mock_sleep:
            download.download_file("https://example.com/runs.geojson", dest, retries=3)

    assert dest.read_bytes() == b"{}"
    mock_sleep.assert_called_once()


def test_download_file_gives_up_after_retries(tmp_path):
    dest = tmp_path / "lifts.geojson"
    always_fails = FakeResponse([], status_error=requests.ConnectionError("boom"))

    with patch.object(download.requests, "get", return_value=always_fails):
        with patch.object(download.time, "sleep"):
            with pytest.raises(RuntimeError, match="Failed to download"):
                download.download_file("https://example.com/lifts.geojson", dest, retries=2)

    assert not dest.exists()


def test_download_all_skips_existing_files(tmp_path):
    existing = tmp_path / "ski_areas.geojson"
    existing.write_text("cached")

    with patch.object(download, "download_file") as mock_download_file:
        paths = download.download_all(tmp_path)

    assert paths["ski_areas"] == existing
    # ski_areas already exists, so only runs and lifts should trigger a download.
    assert mock_download_file.call_count == 2
