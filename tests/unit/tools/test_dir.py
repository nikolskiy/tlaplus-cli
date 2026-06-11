from tlaplus_cli.cli import app


def test_tools_dir(mock_load_config, mock_cache, runner):
    result = runner.invoke(app, ["tools", "dir"])
    assert result.exit_code == 0
    assert str(mock_cache / "tools") in result.stdout


def test_tools_dir_shows_installed_versions(
    mock_load_config, mock_cache, installed_v180, make_installed_version, runner
):
    """dir lists installed version directories under the TLC cache."""
    # Add another version
    tools_dir = mock_cache / "tools"
    make_installed_version("v1.7.0", "bbbbbbb")

    result = runner.invoke(app, ["tools", "dir"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert str(tools_dir) in lines[0]
    # Entries should be indented and sorted
    assert "  v1.7.0-bbbbbbb" in lines[1]
    assert "  v1.8.0-aaaaaaa" in lines[2]


def test_tools_dir_empty(mock_load_config, mock_cache, runner):
    """dir shows just the path when no versions are installed."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    result = runner.invoke(app, ["tools", "dir"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert str(tools_dir) in lines[0]
