from tlaplus_cli.cli import app


def test_tlc_pin(mock_load_config, mock_cache, installed_v180, runner):
    result = runner.invoke(app, ["tools", "pin", "v1.8.0"])
    assert result.exit_code == 0
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert pin_file.exists()
    assert "v1.8.0-aaaaaaa" in pin_file.read_text()


def test_tlc_pin_not_found(mock_load_config, mock_cache, make_installed_version, runner):
    make_installed_version("v1.7.0", "bbbbbbb")
    result = runner.invoke(app, ["tools", "pin", "v9.9.9"])
    assert result.exit_code == 1


def test_pin_lifecycle_install_install_uninstall(mock_github_api, mock_download, mock_load_config, mock_cache, runner):
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


def test_tlc_pin_no_args(mock_load_config, runner):
    """pin without args should fail."""
    result = runner.invoke(app, ["tools", "pin"])
    assert result.exit_code != 0


def test_tlc_pin_interactive_choice(mock_load_config, mock_cache, make_installed_version, runner, mocker):
    """pin with multiple matches should prompt for choice."""
    make_installed_version("v1.8.0", "aaaaaaa")
    make_installed_version("v1.8.0", "bbbbbbb")

    mocker.patch("typer.prompt", return_value=1)

    result = runner.invoke(app, ["tools", "pin", "v1.8.0"])
    assert result.exit_code == 0
    assert "Multiple versions match" in result.stdout

    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert "v1.8.0-bbbbbbb" in pin_file.read_text()
