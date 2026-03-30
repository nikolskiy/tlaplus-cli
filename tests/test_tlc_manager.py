import json
import shutil
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from tlaplus_cli.cli import app

runner = CliRunner()

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
def mock_cache(mocker, tmp_path):
    """Point cache_dir to a temporary directory."""
    mocker.patch("tlaplus_cli.version_manager.cache_dir", return_value=tmp_path)
    mocker.patch("tlaplus_cli.tlc_manager.cache_dir", return_value=tmp_path)
    return tmp_path


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
        tlc_dir = mock_cache / "tlc"
        version_dir = tlc_dir / f"{target.name}-{target.short_sha}"
        if version_dir.exists() and not force:
            return version_dir
        if version_dir.exists():
            shutil.rmtree(version_dir)
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "tla2tools.jar").write_bytes(b"fake jar content")
        return version_dir

    mocker.patch("tlaplus_cli.tlc_manager.download_version", side_effect=_download)
    return _download


@pytest.fixture
def installed_v180(mock_cache):
    """Create a pre-installed v1.8.0 version directory."""
    tlc_dir = mock_cache / "tlc"
    tlc_dir.mkdir(parents=True, exist_ok=True)
    version_dir = tlc_dir / "v1.8.0-aaaaaaa"
    version_dir.mkdir()
    (version_dir / "tla2tools.jar").write_bytes(b"fake jar")
    return version_dir


# --- list ---


def test_tlc_list_shows_remote(mock_github_api, mock_cache, mock_load_config):
    result = runner.invoke(app, ["tlc", "list"])
    assert result.exit_code == 0
    assert "v1.8.0" in result.stdout
    assert "v1.7.0" in result.stdout
    assert "available" in result.stdout


def test_tlc_list_shows_installed(mock_github_api, mock_cache, mock_load_config, installed_v180):
    result = runner.invoke(app, ["tlc", "list"])
    assert result.exit_code == 0
    assert "installed" in result.stdout


def test_tlc_list_shows_local_only(mock_github_api, mock_cache, mock_load_config):
    tlc_dir = mock_cache / "tlc"
    tlc_dir.mkdir(parents=True, exist_ok=True)
    (tlc_dir / "v1.6.0-aaaaaaa").mkdir()
    result = runner.invoke(app, ["tlc", "list"])
    assert result.exit_code == 0
    assert "local only" in result.stdout


# --- install ---


def test_tlc_install(mock_github_api, mock_download, mock_load_config):
    result = runner.invoke(app, ["tlc", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Download complete" in result.stdout
    assert "Auto-pinning" in result.stdout


def test_tlc_install_selects_latest(mock_github_api, mock_download, mock_load_config):
    result = runner.invoke(app, ["tlc", "install"])
    assert result.exit_code == 0
    assert "selecting latest" in result.stdout


def test_tlc_install_already_installed(mock_github_api, mock_download, mock_load_config, installed_v180, mock_cache):
    # Pin so auto-pin doesn't trigger
    pin_file = mock_cache / "tlc" / "tlc-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tlc", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "already installed" in result.stdout


def test_tlc_install_force(mock_github_api, mock_download, mock_load_config, installed_v180, mock_cache):
    pin_file = mock_cache / "tlc" / "tlc-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tlc", "install", "v1.8.0", "--force"])
    assert result.exit_code == 0
    assert "already installed" not in result.stdout
    assert "Download complete" in result.stdout


def test_tlc_install_auto_pins_first(mock_github_api, mock_download, mock_load_config, mock_cache):
    result = runner.invoke(app, ["tlc", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout
    pin_file = mock_cache / "tlc" / "tlc-pinned-version.txt"
    assert pin_file.exists()
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


# --- upgrade ---


def test_tlc_upgrade(mock_github_api, mock_download, mock_load_config, mock_cache):
    # Install an old version with different sha
    tlc_dir = mock_cache / "tlc"
    tlc_dir.mkdir(parents=True, exist_ok=True)
    old_dir = tlc_dir / "v1.8.0-ccccccc"
    old_dir.mkdir()
    (old_dir / "tla2tools.jar").write_bytes(b"old jar")
    # Pin it
    (tlc_dir / "tlc-pinned-version.txt").write_text("v1.8.0-ccccccc")

    result = runner.invoke(app, ["tlc", "upgrade"])
    assert result.exit_code == 0
    assert not old_dir.exists()
    new_dir = tlc_dir / "v1.8.0-aaaaaaa"
    assert new_dir.exists()
    assert (tlc_dir / "tlc-pinned-version.txt").read_text().strip() == "v1.8.0-aaaaaaa"


def test_tlc_upgrade_already_up_to_date(mock_github_api, mock_cache, mock_load_config, installed_v180):
    pin_file = mock_cache / "tlc" / "tlc-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tlc", "upgrade"])
    assert result.exit_code == 0
    assert "already up to date" in result.stdout


# --- path (renamed from find) ---


def test_tlc_path_pinned_with_metadata(mock_load_config, mock_cache, installed_v180):
    """path shows TLC2 version string from metadata then the jar path."""
    pin_file = mock_cache / "tlc" / "tlc-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    # Write metadata

    meta = {"tlc2_version_string": "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"}
    (installed_v180 / "meta-tla2tools.json").write_text(json.dumps(meta))

    result = runner.invoke(app, ["tlc", "path"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert lines[0] == "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"
    assert "tla2tools.jar" in lines[1]


def test_tlc_path_pinned_without_metadata(mock_load_config, mock_cache, installed_v180):
    """path still works when no metadata exists — just shows the jar path."""
    pin_file = mock_cache / "tlc" / "tlc-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")

    result = runner.invoke(app, ["tlc", "path"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "tla2tools.jar" in lines[0]


def test_tlc_path_version_with_metadata(mock_load_config, mock_cache, installed_v180):
    """path <version> shows metadata + jar path for a specific installed version."""

    meta = {"tlc2_version_string": "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"}
    (installed_v180 / "meta-tla2tools.json").write_text(json.dumps(meta))

    result = runner.invoke(app, ["tlc", "path", "v1.8.0"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert lines[0] == "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"
    assert "tla2tools.jar" in lines[1]


def test_tlc_path_version_without_metadata(mock_load_config, mock_cache, installed_v180):
    """path <version> works without metadata — just shows jar path."""
    result = runner.invoke(app, ["tlc", "path", "v1.8.0"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "tla2tools.jar" in lines[0]


def test_tlc_path_not_found(mock_load_config, mock_cache):
    (mock_cache / "tlc").mkdir(parents=True, exist_ok=True)
    result = runner.invoke(app, ["tlc", "path", "v9.9.9"])
    assert result.exit_code == 1


def test_tlc_path_no_pinned(mock_load_config, mock_cache):
    """path without args fails if nothing is pinned."""
    (mock_cache / "tlc").mkdir(parents=True, exist_ok=True)
    result = runner.invoke(app, ["tlc", "path"])
    assert result.exit_code == 1
    assert "No pinned version" in result.output


# --- pin ---


def test_tlc_pin(mock_load_config, mock_cache, installed_v180):
    result = runner.invoke(app, ["tlc", "pin", "v1.8.0"])
    assert result.exit_code == 0
    pin_file = mock_cache / "tlc" / "tlc-pinned-version.txt"
    assert pin_file.exists()
    assert "v1.8.0-aaaaaaa" in pin_file.read_text()


def test_tlc_pin_not_found(mock_load_config, mock_cache):
    tlc_dir = mock_cache / "tlc"
    tlc_dir.mkdir(parents=True, exist_ok=True)
    (tlc_dir / "v1.7.0-bbbbbbb").mkdir()
    result = runner.invoke(app, ["tlc", "pin", "v9.9.9"])
    assert result.exit_code == 1


# --- dir ---


def test_tlc_dir(mock_load_config, mock_cache):
    result = runner.invoke(app, ["tlc", "dir"])
    assert result.exit_code == 0
    assert str(mock_cache / "tlc") in result.stdout


def test_tlc_dir_shows_installed_versions(mock_load_config, mock_cache, installed_v180):
    """dir lists installed version directories under the TLC cache."""
    # Add another version
    tlc_dir = mock_cache / "tlc"
    v170_dir = tlc_dir / "v1.7.0-bbbbbbb"
    v170_dir.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["tlc", "dir"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert str(tlc_dir) in lines[0]
    # Entries should be indented and sorted
    assert "  v1.7.0-bbbbbbb" in lines[1]
    assert "  v1.8.0-aaaaaaa" in lines[2]


def test_tlc_dir_empty(mock_load_config, mock_cache):
    """dir shows just the path when no versions are installed."""
    tlc_dir = mock_cache / "tlc"
    tlc_dir.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(app, ["tlc", "dir"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert str(tlc_dir) in lines[0]


# --- uninstall ---


def test_tlc_uninstall(mock_load_config, mock_cache, installed_v180):
    result = runner.invoke(app, ["tlc", "uninstall", "v1.8.0"])
    assert result.exit_code == 0
    assert not installed_v180.exists()


def test_tlc_uninstall_pinned_warns(mock_load_config, mock_cache, installed_v180):
    pin_file = mock_cache / "tlc" / "tlc-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tlc", "uninstall", "v1.8.0"], input="y\n")
    assert result.exit_code == 0
    assert "pinned" in result.stdout.lower()
    assert not pin_file.exists()
    assert not installed_v180.exists()


def test_tlc_uninstall_default(mock_load_config, mock_cache):
    legacy = mock_cache / "tla2tools.jar"
    legacy.write_bytes(b"legacy jar")
    result = runner.invoke(app, ["tlc", "uninstall", "default"])
    assert result.exit_code == 0
    assert not legacy.exists()


# --- fetch-cache ---


def test_fetch_cache_clear(mock_load_config, mock_cache):
    cache_file = mock_cache / "github_cache.json"
    cache_file.write_text("{}")
    result = runner.invoke(app, ["fetch-cache", "clear"])
    assert result.exit_code == 0
    assert not cache_file.exists()


# --- meta ---


def test_tlc_meta_sync(mock_github_api, mock_cache, mock_load_config, installed_v180, mocker):
    mock_write = mocker.patch("tlaplus_cli.tlc_manager.write_version_metadata")
    result = runner.invoke(app, ["tlc", "meta", "sync"])
    assert result.exit_code == 0
    assert "Synced metadata for v1.8.0-aaaaaaa" in result.stdout
    mock_write.assert_called_once()
    args, _ = mock_write.call_args
    assert args[0] == installed_v180
    assert args[1].name == "v1.8.0"
