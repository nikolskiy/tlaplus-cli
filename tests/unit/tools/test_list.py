from tlaplus_cli.cli import app


def test_tlc_list_shows_remote(mock_github_api, mock_cache, mock_load_config, runner):
    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "v1.8.0" in result.stdout
    assert "v1.7.0" in result.stdout
    assert "available" in result.stdout


def test_tlc_list_shows_installed(mock_github_api, mock_cache, mock_load_config, installed_v180, runner):
    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "installed" in result.stdout


def test_tlc_list_shows_local_only(mock_github_api, mock_cache, mock_load_config, make_installed_version, runner):
    make_installed_version("v1.6.0", "aaaaaaa")
    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "local only" in result.stdout


def test_tlc_list_enhanced(mock_github_api, mock_cache, mock_load_config, make_installed_version, runner):
    # Local version v1.8.0 with DIFFERENT SHA
    make_installed_version("v1.8.0", "ccccccc", meta={"published_at": "2023-12-31T00:00:00Z"})

    # Pin v1.8.0-ccccccc
    tools_dir = mock_cache / "tools"
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


def test_list_shows_url_installed_version(
    mock_github_api, mock_cache, mock_load_config, make_installed_version, runner
):
    """URL-installed version (timestamp tag) appears correctly in tla tools list."""
    ts = "2026-04-06T12:51:28Z"
    make_installed_version("v1.9.0", ts)

    result = runner.invoke(app, ["tools", "list"])
    assert result.exit_code == 0
    assert "v1.9.0" in result.stdout
    assert ts in result.stdout
    assert "local only" in result.stdout
