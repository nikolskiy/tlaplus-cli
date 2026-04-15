from tlaplus_cli.cli import app


def test_tlc_meta_sync(mock_github_api, mock_cache, mock_load_config, installed_v180, mocker, runner):
    mock_write = mocker.patch("tlaplus_cli.tools_manager.write_version_metadata")
    result = runner.invoke(app, ["tools", "meta", "sync"])
    assert result.exit_code == 0
    assert "Synced metadata for v1.8.0-aaaaaaa" in result.stdout
    mock_write.assert_called_once()
    args, _ = mock_write.call_args
    assert args[0] == installed_v180
    assert args[1].name == "v1.8.0"


def test_meta_sync_skips_url_installed_version(
    mock_github_api, mock_cache, mock_load_config, mocker, make_installed_version, runner
):
    """meta sync gracefully skips versions not found in the remote list."""
    ts = "2026-04-06T12:51:28Z"
    make_installed_version("v1.9.0", ts)

    mocker.patch("tlaplus_cli.tools_manager.write_version_metadata")

    result = runner.invoke(app, ["tools", "meta", "sync"])
    assert result.exit_code == 0
    assert "Could not find remote data for v1.9.0" in result.output
