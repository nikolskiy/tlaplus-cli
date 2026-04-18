import json
import os
import time

from tlaplus_cli.cli import app
from tlaplus_cli.version_manager import FetchStatus, fetch_remote_versions


def test_fetch_cache_clear(mock_load_config, mock_cache, runner):
    cache_file = mock_cache / "github_cache.json"
    cache_file.write_text("{}")
    result = runner.invoke(app, ["fetch-cache", "clear"])
    assert result.exit_code == 0
    assert not cache_file.exists()


def test_fetch_cache_clear_idempotent(mock_load_config, mock_cache, runner):
    """Clearing a non-existent cache should not fail."""
    cache_file = mock_cache / "github_cache.json"
    assert not cache_file.exists()
    result = runner.invoke(app, ["fetch-cache", "clear"])
    assert result.exit_code == 0
    assert "cache cleared" in result.stdout.lower()


def test_fetch_remote_versions_uses_cache(mocker, mock_cache, base_settings):
    """fetch_remote_versions returns cached data if not stale."""
    cache_file = mock_cache / "github_cache.json"
    mock_data = [
        {
            "name": "v1.8.0",
            "short_sha": "aaaaaaa",
            "full_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "jar_download_url": "http://example.com/jar",
            "published_at": "2024-01-01T00:00:00Z",
            "prerelease": False,
        }
    ]
    cache_file.write_text(json.dumps(mock_data))

    # Set mtime to now (fresh cache)
    now = time.time()
    os.utime(cache_file, (now, now))

    mock_get = mocker.patch("requests.get")

    versions, status = fetch_remote_versions(base_settings.tla.urls.tags, base_settings.tla.urls.releases)

    assert status == FetchStatus.CACHED
    assert len(versions) == 1
    assert versions[0].name == "v1.8.0"
    mock_get.assert_not_called()


def test_fetch_remote_versions_stale_fallback(mocker, mock_cache, base_settings):
    """fetch_remote_versions falls back to stale cache if API fails."""
    cache_file = mock_cache / "github_cache.json"
    mock_data = [
        {
            "name": "v1.7.0",
            "short_sha": "bbbbbbb",
            "full_sha": "bbb",
            "jar_download_url": "url",
            "published_at": "date",
            "prerelease": False,
        }
    ]
    cache_file.write_text(json.dumps(mock_data))

    # Set mtime to long ago (stale)
    old_time = time.time() - 7200  # 2 hours ago
    os.utime(cache_file, (old_time, old_time))

    # Mock API failure
    mocker.patch("requests.get", side_effect=Exception("API down"))

    versions, status = fetch_remote_versions(base_settings.tla.urls.tags, base_settings.tla.urls.releases)

    assert status == FetchStatus.STALE
    assert len(versions) == 1
    assert versions[0].name == "v1.7.0"


def test_fetch_remote_versions_corrupt_cache(mocker, mock_cache, base_settings):
    """fetch_remote_versions handles corrupt cache file."""
    cache_file = mock_cache / "github_cache.json"
    cache_file.write_text("not json")

    # Mock API failure to see if it handles corrupt cache during fallback
    mocker.patch("requests.get", side_effect=Exception("API down"))

    versions, status = fetch_remote_versions(base_settings.tla.urls.tags, base_settings.tla.urls.releases)

    assert status == FetchStatus.UNAVAILABLE
    assert versions == []
