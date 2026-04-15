import shutil
from unittest.mock import MagicMock

import pytest

MOCK_TAGS = [
    {"name": "v1.8.0", "commit": {"sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}},
    {"name": "v1.7.0", "commit": {"sha": "bbbbbbb890aaaaaaa234567890aaaaaaa2345678"}},
]

MOCK_RELEASES = [
    {
        "tag_name": "v1.8.0",
        "assets": [{"name": "tla2tools.jar", "browser_download_url": "https://example.com/v1.8.0/tla2tools.jar"}],
    },
    {
        "tag_name": "v1.7.0",
        "assets": [{"name": "tla2tools.jar", "browser_download_url": "https://example.com/v1.7.0/tla2tools.jar"}],
    },
]


@pytest.fixture
def mock_github_api(mocker):
    """Mock GitHub API responses for tags and releases."""
    mock_tags = MagicMock()
    mock_tags.json.return_value = MOCK_TAGS
    mock_tags.raise_for_status = MagicMock()

    mock_releases = MagicMock()
    mock_releases.json.return_value = MOCK_RELEASES
    mock_releases.raise_for_status = MagicMock()

    def side_effect(url, **kwargs):
        if "tags" in url:
            return mock_tags
        return mock_releases

    mocker.patch("tlaplus_cli.version_manager.requests.get", side_effect=side_effect)


@pytest.fixture
def mock_download(mocker, mock_cache):
    """Mock download_version to create a directory with a dummy jar."""

    def _download(target, *, force=False):
        tools_dir = mock_cache / "tools"
        version_dir = tools_dir / f"{target.name}-{target.short_sha}"
        if version_dir.exists() and not force:
            return version_dir
        if version_dir.exists():
            shutil.rmtree(version_dir)
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "tla2tools.jar").write_bytes(b"fake jar content")
        return version_dir

    mocker.patch("tlaplus_cli.tools_manager.download_version", side_effect=_download)
    return _download


@pytest.fixture
def installed_v180(mock_cache):
    """Create a pre-installed v1.8.0 version directory."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    version_dir = tools_dir / "v1.8.0-aaaaaaa"
    version_dir.mkdir()
    (version_dir / "tla2tools.jar").write_bytes(b"fake jar")
    return version_dir
