from tlaplus_cli.cli import app


def test_uninstall_pinned_falls_back_to_latest(mock_load_config, mock_cache, make_installed_version, runner):
    """Uninstalling the pinned version re-pins to the latest remaining."""
    # Install two versions
    make_installed_version("v1.8.0", "aaaaaaa")
    v170 = make_installed_version("v1.7.0", "bbbbbbb")

    # Pin v1.7.0
    tools_dir = mock_cache / "tools"
    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text("v1.7.0-bbbbbbb")

    result = runner.invoke(app, ["tools", "uninstall", "v1.7.0"], input="y\n")
    assert result.exit_code == 0
    assert not v170.exists()

    # Pin should fall back to v1.8.0
    assert pin_file.exists()
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_uninstall_pinned_last_version_clears_pin(mock_load_config, mock_cache, make_installed_version, runner):
    """Uninstalling the only installed version removes the pin entirely."""
    v180 = make_installed_version("v1.8.0", "aaaaaaa")

    tools_dir = mock_cache / "tools"
    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")

    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0"], input="y\n")
    assert result.exit_code == 0
    assert not v180.exists()
    assert not pin_file.exists()


def test_uninstall_non_pinned_keeps_pin(mock_load_config, mock_cache, make_installed_version, runner):
    """Uninstalling a version that is NOT pinned leaves the pin unchanged."""
    make_installed_version("v1.8.0", "aaaaaaa")
    v170 = make_installed_version("v1.7.0", "bbbbbbb")

    tools_dir = mock_cache / "tools"
    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")

    # This doesn't need input="y\n" because it's not the pinned version.
    result = runner.invoke(app, ["tools", "uninstall", "v1.7.0"])
    assert result.exit_code == 0
    assert not v170.exists()

    # Pin should remain on v1.8.0
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_uninstall_pinned_fallback_uses_metadata_date(mock_load_config, mock_cache, make_installed_version, runner):
    """Fallback prefers the version with a later published_at when semver is equal."""
    # Two tags of v1.8.0 with different SHAs
    make_installed_version("v1.8.0", "aaaaaaa", meta={"published_at": "2024-01-01T00:00:00Z"})
    make_installed_version("v1.8.0", "bbbbbbb", meta={"published_at": "2025-06-15T00:00:00Z"})

    # Pin the first, then a third version which we'll uninstall
    make_installed_version("v1.7.0", "ccccccc")

    tools_dir = mock_cache / "tools"
    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text("v1.7.0-ccccccc")

    result = runner.invoke(app, ["tools", "uninstall", "v1.7.0"], input="y\n")
    assert result.exit_code == 0

    # Should fall back to the v1.8.0 tag with the later published_at (bbbbbbb)
    assert pin_file.read_text().strip() == "v1.8.0-bbbbbbb"


def test_tlc_uninstall(mock_load_config, mock_cache, installed_v180, runner):
    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0"])
    assert result.exit_code == 0
    assert not installed_v180.exists()


def test_tlc_uninstall_pinned_warns(mock_load_config, mock_cache, installed_v180, runner):
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0"], input="y\n")
    assert result.exit_code == 0
    assert "pinned" in result.stdout.lower()
    assert not pin_file.exists()
    assert not installed_v180.exists()


def test_tlc_uninstall_default(mock_load_config, mock_cache, runner):
    legacy = mock_cache / "tla2tools.jar"
    legacy.write_bytes(b"legacy jar")
    result = runner.invoke(app, ["tools", "uninstall", "default"])
    assert result.exit_code == 0
    assert not legacy.exists()


def test_uninstall_interactive_choice(mock_cache, mocker, make_installed_version, runner, mock_load_config):
    # Install two tags of v1.8.0
    v1 = make_installed_version("v1.8.0", "aaaaaaa")
    v2 = make_installed_version("v1.8.0", "bbbbbbb")

    # Mock typer.prompt to select choice 1 (v1.8.0-bbbbbbb)
    mocker.patch("typer.prompt", return_value=1)

    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0"])
    assert result.exit_code == 0
    assert "Multiple versions match" in result.stdout
    assert not v2.exists()
    assert v1.exists()


def test_uninstall_all_flag(mock_cache, make_installed_version, runner, mock_load_config):
    # Install two tags of v1.8.0
    v1 = make_installed_version("v1.8.0", "aaaaaaa")
    v2 = make_installed_version("v1.8.0", "bbbbbbb")

    result = runner.invoke(app, ["tools", "uninstall", "v1.8.0", "--all", "-y"])
    assert result.exit_code == 0
    assert not v1.exists()
    assert not v2.exists()
