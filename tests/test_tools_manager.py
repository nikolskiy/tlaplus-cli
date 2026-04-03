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
    mocker.patch("tlaplus_cli.tools_manager.cache_dir", return_value=tmp_path)
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


# --- list ---


def test_tlc_list_shows_remote(mock_github_api, mock_cache, mock_load_config):
    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "v1.8.0" in result.stdout
    assert "v1.7.0" in result.stdout
    assert "available" in result.stdout


def test_tlc_list_shows_installed(mock_github_api, mock_cache, mock_load_config, installed_v180):
    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "installed" in result.stdout


def test_tlc_list_shows_local_only(mock_github_api, mock_cache, mock_load_config):
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "v1.6.0-aaaaaaa").mkdir()
    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "local only" in result.stdout


# --- install ---


def test_tlc_install(mock_github_api, mock_download, mock_load_config):
    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Download complete" in result.stdout
    assert "Auto-pinning" in result.stdout


def test_tlc_install_selects_latest(mock_github_api, mock_download, mock_load_config):
    result = runner.invoke(app, ["tools", "install"])
    assert result.exit_code == 0
    assert "selecting latest" in result.stdout


def test_tlc_install_already_installed(mock_github_api, mock_download, mock_load_config, installed_v180, mock_cache):
    # Pin so auto-pin doesn't trigger
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "already installed" in result.stdout


def test_tlc_install_force(mock_github_api, mock_download, mock_load_config, installed_v180, mock_cache):
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tools", "install", "v1.8.0", "--force"])
    assert result.exit_code == 0
    assert "already installed" not in result.stdout
    assert "Download complete" in result.stdout


def test_tlc_install_auto_pins_first(mock_github_api, mock_download, mock_load_config, mock_cache):
    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert pin_file.exists()
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_install_second_version_does_not_move_pin(mock_github_api, mock_download, mock_load_config, mock_cache):
    """Installing v1.7.0 after v1.8.0 is pinned must keep pin on v1.8.0."""
    # Install v1.8.0 first — auto-pins
    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout

    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"

    # Install v1.7.0 second — pin should NOT change
    result = runner.invoke(app, ["tools", "install", "v1.7.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" not in result.stdout
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_install_force_does_not_move_pin(mock_github_api, mock_download, mock_load_config, mock_cache):
    """Force-reinstalling a non-pinned version must not hijack the pin."""
    # Install and auto-pin v1.8.0
    runner.invoke(app, ["tools", "install", "v1.8.0"])
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"

    # Install v1.7.0, then force-reinstall it
    runner.invoke(app, ["tools", "install", "v1.7.0"])
    runner.invoke(app, ["tools", "install", "v1.7.0", "--force"])

    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_uninstall_pinned_falls_back_to_latest(mock_load_config, mock_cache):
    """Uninstalling the pinned version re-pins to the latest remaining."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    # Install two versions
    v180 = tools_dir / "v1.8.0-aaaaaaa"
    v180.mkdir()
    (v180 / "tla2tools.jar").write_bytes(b"jar")

    v170 = tools_dir / "v1.7.0-bbbbbbb"
    v170.mkdir()
    (v170 / "tla2tools.jar").write_bytes(b"jar")

    # Pin v1.7.0
    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text("v1.7.0-bbbbbbb")

    result = runner.invoke(app, ["tools", "uninstall", "v1.7.0"], input="y\n")
    assert result.exit_code == 0
    assert not v170.exists()

    # Pin should fall back to v1.8.0
    assert pin_file.exists()
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_uninstall_pinned_last_version_clears_pin(mock_load_config, mock_cache):
    """Uninstalling the only installed version removes the pin entirely."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    v180 = tools_dir / "v1.8.0-aaaaaaa"
    v180.mkdir()
    (v180 / "tla2tools.jar").write_bytes(b"jar")

    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")

    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0"], input="y\n")
    assert result.exit_code == 0
    assert not v180.exists()
    assert not pin_file.exists()


def test_uninstall_non_pinned_keeps_pin(mock_load_config, mock_cache):
    """Uninstalling a version that is NOT pinned leaves the pin unchanged."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    v180 = tools_dir / "v1.8.0-aaaaaaa"
    v180.mkdir()
    (v180 / "tla2tools.jar").write_bytes(b"jar")

    v170 = tools_dir / "v1.7.0-bbbbbbb"
    v170.mkdir()
    (v170 / "tla2tools.jar").write_bytes(b"jar")

    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")

    result = runner.invoke(app, ["tools", "uninstall", "v1.7.0"])
    assert result.exit_code == 0
    assert not v170.exists()

    # Pin should remain on v1.8.0
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_uninstall_pinned_fallback_uses_metadata_date(mock_load_config, mock_cache):
    """Fallback prefers the version with a later published_at when semver is equal."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    # Two tags of v1.8.0 with different SHAs
    v1 = tools_dir / "v1.8.0-aaaaaaa"
    v1.mkdir()
    (v1 / "tla2tools.jar").write_bytes(b"jar")
    (v1 / "meta-tla2tools.json").write_text(json.dumps({"published_at": "2024-01-01T00:00:00Z"}))

    v2 = tools_dir / "v1.8.0-bbbbbbb"
    v2.mkdir()
    (v2 / "tla2tools.jar").write_bytes(b"jar")
    (v2 / "meta-tla2tools.json").write_text(json.dumps({"published_at": "2025-06-15T00:00:00Z"}))

    # Pin the first, then a third version which we'll uninstall
    v170 = tools_dir / "v1.7.0-ccccccc"
    v170.mkdir()
    (v170 / "tla2tools.jar").write_bytes(b"jar")

    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text("v1.7.0-ccccccc")

    result = runner.invoke(app, ["tools", "uninstall", "v1.7.0"], input="y\n")
    assert result.exit_code == 0

    # Should fall back to the v1.8.0 tag with the later published_at (bbbbbbb)
    assert pin_file.read_text().strip() == "v1.8.0-bbbbbbb"


def test_pin_lifecycle_install_install_uninstall(mock_github_api, mock_download, mock_load_config, mock_cache):
    """Full lifecycle: install -> auto-pin -> install second -> pin stable -> uninstall pinned -> fallback."""
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"

    # 1. Install v1.8.0 — auto-pins
    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"

    # 2. Install v1.7.0 — pin unchanged
    result = runner.invoke(app, ["tools", "install", "v1.7.0"])
    assert result.exit_code == 0
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"

    # 3. Uninstall v1.8.0 (pinned) — falls back to v1.7.0
    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0"], input="y\n")
    assert result.exit_code == 0
    assert pin_file.read_text().strip().startswith("v1.7.0")

    # 4. Uninstall v1.7.0 (now pinned) — pin removed entirely
    result = runner.invoke(app, ["tools", "uninstall", "v1.7.0"], input="y\n")
    assert result.exit_code == 0
    assert not pin_file.exists()


def test_install_auto_pins_when_pin_file_missing(mock_github_api, mock_download, mock_load_config, mock_cache):
    """First-ever install creates the pin file automatically."""
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert not pin_file.exists()

    result = runner.invoke(app, ["tools", "install", "v1.7.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout
    assert pin_file.read_text().strip() == "v1.7.0-bbbbbbb"


def test_install_auto_pins_when_pin_file_empty(mock_github_api, mock_download, mock_load_config, mock_cache):
    """An empty (corrupted) pin file is treated as 'no pin'."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "tools-pinned-version.txt").write_text("")

    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout


def test_install_auto_pins_when_pinned_dir_deleted(mock_github_api, mock_download, mock_load_config, mock_cache):
    """Pin file references a directory that no longer exists -> treated as unpinned."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "tools-pinned-version.txt").write_text("v0.0.0-0000000")

    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout


# --- upgrade ---


def test_tlc_upgrade(mock_github_api, mock_download, mock_load_config, mock_cache):
    # Install an old version with different sha
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    old_dir = tools_dir / "v1.8.0-ccccccc"
    old_dir.mkdir()
    (old_dir / "tla2tools.jar").write_bytes(b"old jar")
    # Pin it
    (tools_dir / "tools-pinned-version.txt").write_text("v1.8.0-ccccccc")

    result = runner.invoke(app, ["tools", "upgrade"])
    assert result.exit_code == 0
    assert not old_dir.exists()
    new_dir = tools_dir / "v1.8.0-aaaaaaa"
    assert new_dir.exists()
    assert (tools_dir / "tools-pinned-version.txt").read_text().strip() == "v1.8.0-aaaaaaa"


def test_tlc_upgrade_already_up_to_date(mock_github_api, mock_cache, mock_load_config, installed_v180):
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tools", "upgrade"])
    assert result.exit_code == 0
    assert "already up to date" in result.stdout


# --- path (renamed from find) ---


def test_tlc_path_pinned_with_metadata(mock_load_config, mock_cache, installed_v180):
    """path shows TLC2 version string from metadata then the jar path."""
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    # Write metadata

    meta = {"tlc2_version_string": "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"}
    (installed_v180 / "meta-tla2tools.json").write_text(json.dumps(meta))

    result = runner.invoke(app, ["tools", "path"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert lines[0] == "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"
    assert "tla2tools.jar" in lines[1]


def test_tlc_path_pinned_without_metadata(mock_load_config, mock_cache, installed_v180):
    """path still works when no metadata exists — just shows the jar path."""
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")

    result = runner.invoke(app, ["tools", "path"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "tla2tools.jar" in lines[0]


def test_tlc_path_version_with_metadata(mock_load_config, mock_cache, installed_v180):
    """path <version> shows metadata + jar path for a specific installed version."""

    meta = {"tlc2_version_string": "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"}
    (installed_v180 / "meta-tla2tools.json").write_text(json.dumps(meta))

    result = runner.invoke(app, ["tools", "path", "v1.8.0"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert lines[0] == "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"
    assert "tla2tools.jar" in lines[1]


def test_tlc_path_version_without_metadata(mock_load_config, mock_cache, installed_v180):
    """path <version> works without metadata — just shows jar path."""
    result = runner.invoke(app, ["tools", "path", "v1.8.0"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "tla2tools.jar" in lines[0]


def test_tlc_path_not_found(mock_load_config, mock_cache):
    (mock_cache / "tlc").mkdir(parents=True, exist_ok=True)
    result = runner.invoke(app, ["tools", "path", "v9.9.9"])
    assert result.exit_code == 1


def test_tlc_path_no_pinned(mock_load_config, mock_cache):
    """path without args fails if nothing is pinned."""
    (mock_cache / "tlc").mkdir(parents=True, exist_ok=True)
    result = runner.invoke(app, ["tools", "path"])
    assert result.exit_code == 1
    assert "No pinned version" in result.output


# --- pin ---


def test_tlc_pin(mock_load_config, mock_cache, installed_v180):
    result = runner.invoke(app, ["tools", "pin", "v1.8.0"])
    assert result.exit_code == 0
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert pin_file.exists()
    assert "v1.8.0-aaaaaaa" in pin_file.read_text()


def test_tlc_pin_not_found(mock_load_config, mock_cache):
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "v1.7.0-bbbbbbb").mkdir()
    result = runner.invoke(app, ["tools", "pin", "v9.9.9"])
    assert result.exit_code == 1


# --- dir ---


def test_tools_dir(mock_load_config, mock_cache):
    result = runner.invoke(app, ["tools", "dir"])
    assert result.exit_code == 0
    assert str(mock_cache / "tools") in result.stdout


def test_tools_dir_shows_installed_versions(mock_load_config, mock_cache, installed_v180):
    """dir lists installed version directories under the TLC cache."""
    # Add another version
    tools_dir = mock_cache / "tools"
    v170_dir = tools_dir / "v1.7.0-bbbbbbb"
    v170_dir.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["tools", "dir"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert str(tools_dir) in lines[0]
    # Entries should be indented and sorted
    assert "  v1.7.0-bbbbbbb" in lines[1]
    assert "  v1.8.0-aaaaaaa" in lines[2]


def test_tools_dir_empty(mock_load_config, mock_cache):
    """dir shows just the path when no versions are installed."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(app, ["tools", "dir"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert str(tools_dir) in lines[0]


# --- uninstall ---


def test_tlc_uninstall(mock_load_config, mock_cache, installed_v180):
    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0"])
    assert result.exit_code == 0
    assert not installed_v180.exists()


def test_tlc_uninstall_pinned_warns(mock_load_config, mock_cache, installed_v180):
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0"], input="y\n")
    assert result.exit_code == 0
    assert "pinned" in result.stdout.lower()
    assert not pin_file.exists()
    assert not installed_v180.exists()


def test_tlc_uninstall_default(mock_load_config, mock_cache):
    legacy = mock_cache / "tla2tools.jar"
    legacy.write_bytes(b"legacy jar")
    result = runner.invoke(app, ["tools", "uninstall", "default"])
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
    mock_write = mocker.patch("tlaplus_cli.tools_manager.write_version_metadata")
    result = runner.invoke(app, ["tools", "meta", "sync"])
    assert result.exit_code == 0
    assert "Synced metadata for v1.8.0-aaaaaaa" in result.stdout
    mock_write.assert_called_once()
    args, _ = mock_write.call_args
    assert args[0] == installed_v180
    assert args[1].name == "v1.8.0"


def test_tlc_list_enhanced(mock_github_api, mock_cache, mock_load_config):
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    # Local version v1.8.0 with DIFFERENT SHA
    v180_local = tools_dir / "v1.8.0-ccccccc"
    v180_local.mkdir()
    (v180_local / "meta-tla2tools.json").write_text(json.dumps({"published_at": "2023-12-31T00:00:00Z"}))

    # Pin v1.8.0-ccccccc
    (tools_dir / "tools-pinned-version.txt").write_text("v1.8.0-ccccccc")

    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0

    # Check for "Published" column header
    assert "Published" in result.stdout

    # Check that "upgrade" status is GONE
    assert "upgrade" not in result.stdout

    # Check for two entries for v1.8.0
    assert "aaaaaaa" in result.stdout
    assert "ccccccc" in result.stdout
    assert "available" in result.stdout
    assert "installed" in result.stdout

    # Check for green checkmark
    assert "✓" in result.stdout


def test_upgrade_missing_local_version_triggers_install(mock_github_api, mock_cache, mock_load_config, mocker):
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    # Mock download_version
    def side_effect(target, **kwargs):
        new_dir = tools_dir / f"{target.name}-{target.short_sha}"
        new_dir.mkdir(parents=True, exist_ok=True)
        (new_dir / "tla2tools.jar").write_text("new jar")
        return new_dir

    mocker.patch("tlaplus_cli.tools_manager.download_version", side_effect=side_effect)

    # v1.8.0 is NOT installed locally
    result = runner.invoke(app, ["tools", "upgrade", "v1.8.0"])
    assert result.exit_code == 0
    assert "not found locally. Installing instead." in result.stdout
    assert (tools_dir / "v1.8.0-aaaaaaa").exists()


def test_uninstall_interactive_choice(mock_cache, mocker):
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    # Install two tags of v1.8.0
    v1 = tools_dir / "v1.8.0-aaaaaaa"
    v1.mkdir()
    v2 = tools_dir / "v1.8.0-bbbbbbb"
    v2.mkdir()

    # Mock typer.prompt to select choice 1 (v1.8.0-bbbbbbb)
    mocker.patch("typer.prompt", return_value=1)

    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0"])
    assert result.exit_code == 0
    assert "Multiple versions match" in result.stdout
    assert not v2.exists()
    assert v1.exists()


def test_uninstall_all_flag(mock_cache):
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    # Install two tags of v1.8.0
    v1 = tools_dir / "v1.8.0-aaaaaaa"
    v1.mkdir()
    v2 = tools_dir / "v1.8.0-bbbbbbb"
    v2.mkdir()

    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0", "--all"])
    assert result.exit_code == 0
    assert not v1.exists()
    assert not v2.exists()
