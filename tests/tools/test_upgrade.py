import shutil

import pytest
import typer

from tlaplus_cli.cli import app
from tlaplus_cli.tools_manager import _resolve_upgrade_target


def test_tlc_upgrade(mock_github_api, mock_download, mock_load_config, mock_cache, make_installed_version, runner):
    # Install an old version with different sha
    old_dir = make_installed_version("v1.8.0", "ccccccc")
    # Pin it
    tools_dir = mock_cache / "tools"
    (tools_dir / "tools-pinned-version.txt").write_text("v1.8.0-ccccccc")

    result = runner.invoke(app, ["tools", "upgrade"])
    assert result.exit_code == 0
    assert not old_dir.exists()
    new_dir = tools_dir / "v1.8.0-aaaaaaa"
    assert new_dir.exists()
    assert (tools_dir / "tools-pinned-version.txt").read_text().strip() == "v1.8.0-aaaaaaa"


def test_tlc_upgrade_already_up_to_date(mock_github_api, mock_cache, mock_load_config, installed_v180, runner):
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tools", "upgrade"])
    assert result.exit_code == 0
    assert "already up to date" in result.stdout


def test_upgrade_missing_local_version_triggers_install(mock_github_api, mock_cache, mock_load_config, mocker, runner):
    """If the target version for upgrade is not found locally, it should trigger an install."""
    # Ensure nothing is installed or pinned
    tools_dir = mock_cache / "tools"
    if tools_dir.exists():
        shutil.rmtree(tools_dir)

    result = runner.invoke(app, ["tools", "upgrade", "v1.8.0"])
    assert result.exit_code == 0
    assert "not found locally. Installing instead." in result.stdout
    assert (tools_dir / "v1.8.0-aaaaaaa").exists()


def test_resolve_upgrade_target_with_version(mock_cache, make_installed_version):
    v180_dir = make_installed_version("v1.8.0", "aaaaaaa")

    # Existing version
    name, path = _resolve_upgrade_target("v1.8.0", None)
    assert name == "v1.8.0"
    assert path == v180_dir

    # Missing version
    name, path = _resolve_upgrade_target("v1.7.0", None)
    assert name == "v1.7.0"
    assert path is None


def test_resolve_upgrade_target_with_pinned(mock_cache, make_installed_version):
    v180_dir = make_installed_version("v1.8.0", "aaaaaaa")

    name, path = _resolve_upgrade_target(None, v180_dir)
    assert name == "v1.8.0"
    assert path == v180_dir


def test_resolve_upgrade_target_no_args_no_pin(runner):
    with pytest.raises(typer.Exit):
        _resolve_upgrade_target(None, None)
