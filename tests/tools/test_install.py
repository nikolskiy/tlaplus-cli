from tlaplus_cli.cli import app


def test_tlc_install(mock_github_api, mock_download, mock_load_config, runner):
    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Download complete" in result.stdout
    assert "Auto-pinning" in result.stdout


def test_tlc_install_selects_latest(mock_github_api, mock_download, mock_load_config, runner):
    result = runner.invoke(app, ["tools", "install"])
    assert result.exit_code == 0
    assert "selecting latest" in result.stdout


def test_tlc_install_already_installed(
    mock_github_api, mock_download, mock_load_config, installed_v180, mock_cache, runner
):
    # Pin so auto-pin doesn't trigger
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "already installed" in result.stdout


def test_tlc_install_force(mock_github_api, mock_download, mock_load_config, installed_v180, mock_cache, runner):
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    result = runner.invoke(app, ["tools", "install", "v1.8.0", "--force"])
    assert result.exit_code == 0
    assert "already installed" not in result.stdout
    assert "Download complete" in result.stdout


def test_tlc_install_auto_pins_first(mock_github_api, mock_download, mock_load_config, mock_cache, runner):
    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert pin_file.exists()
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_install_second_version_does_not_move_pin(mock_github_api, mock_download, mock_load_config, mock_cache, runner):
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


def test_install_force_does_not_move_pin(mock_github_api, mock_download, mock_load_config, mock_cache, runner):
    """Force-reinstalling a non-pinned version must not hijack the pin."""
    # Install and auto-pin v1.8.0
    runner.invoke(app, ["tools", "install", "v1.8.0"])
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"

    # Install v1.7.0, then force-reinstall it
    runner.invoke(app, ["tools", "install", "v1.7.0"])
    runner.invoke(app, ["tools", "install", "v1.7.0", "--force"])

    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_install_auto_pins_when_pin_file_missing(mock_github_api, mock_download, mock_load_config, mock_cache, runner):
    """First-ever install creates the pin file automatically."""
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert not pin_file.exists()

    result = runner.invoke(app, ["tools", "install", "v1.7.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout
    assert pin_file.read_text().strip() == "v1.7.0-bbbbbbb"


def test_install_auto_pins_when_pin_file_empty(mock_github_api, mock_download, mock_load_config, mock_cache, runner):
    """An empty (corrupted) pin file is treated as 'no pin'."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "tools-pinned-version.txt").write_text("")

    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout


def test_install_auto_pins_when_pinned_dir_deleted(
    mock_github_api, mock_download, mock_load_config, mock_cache, runner
):
    """Pin file references a directory that no longer exists -> treated as unpinned."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "tools-pinned-version.txt").write_text("v0.0.0-0000000")

    result = runner.invoke(app, ["tools", "install", "v1.8.0"])
    assert result.exit_code == 0
    assert "Auto-pinning" in result.stdout


# --- Custom URL install CLI tests ---


def test_install_from_url_success(mock_cache, mock_load_config, mocker, runner):
    """Installing from a valid URL echoes 'Download complete' and auto-pins."""
    url = "https://example.com/v1.9.0/tla2tools.jar"
    fake_ts = "2026-04-06T12:51:28Z"

    def _fake_download_url(u):
        tools_dir = mock_cache / "tools"
        version_dir = tools_dir / f"v1.9.0-{fake_ts}"
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "tla2tools.jar").write_bytes(b"jar")
        return version_dir

    mocker.patch(
        "tlaplus_cli.cmd.tools.install.download_version_from_url",
        side_effect=_fake_download_url,
    )

    result = runner.invoke(app, ["tools", "install", url])
    assert result.exit_code == 0
    assert "Download complete" in result.stdout
    assert "Auto-pinning" in result.stdout

    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    assert pin_file.read_text().strip() == f"v1.9.0-{fake_ts}"


def test_install_from_url_no_version_segment(mock_cache, mock_load_config, mocker, runner):
    """A URL without a semver segment prints an error and exits with code 1."""
    url = "https://example.com/latest/tla2tools.jar"

    mocker.patch(
        "tlaplus_cli.cmd.tools.install.download_version_from_url",
        side_effect=ValueError(
            'could not extract a version name from the URL. The URL must contain a version segment (e.g. "v1.8.0").'
        ),
    )

    result = runner.invoke(app, ["tools", "install", url])
    assert result.exit_code == 1
    assert "could not extract a version name" in result.output


def test_install_from_url_does_not_move_existing_pin(mock_cache, mock_load_config, mocker, runner):
    """URL install does NOT auto-pin when a pin already exists."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    (tools_dir / "v1.8.0-aaaaaaa").mkdir()

    url = "https://example.com/v1.9.0/tla2tools.jar"
    fake_ts = "2026-04-06T12:51:28Z"

    def _fake_download_url(u):
        version_dir = tools_dir / f"v1.9.0-{fake_ts}"
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "tla2tools.jar").write_bytes(b"jar")
        return version_dir

    mocker.patch(
        "tlaplus_cli.cmd.tools.install.download_version_from_url",
        side_effect=_fake_download_url,
    )

    result = runner.invoke(app, ["tools", "install", url])
    assert result.exit_code == 0
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"
    assert "Auto-pinning" not in result.stdout


def test_install_from_url_network_error(mock_cache, mock_load_config, mocker, runner):
    """A network error during URL download prints the error and exits with code 1."""
    url = "https://example.com/v1.9.0/tla2tools.jar"

    mocker.patch(
        "tlaplus_cli.cmd.tools.install.download_version_from_url",
        side_effect=Exception("connection refused"),
    )

    result = runner.invoke(app, ["tools", "install", url])
    assert result.exit_code == 1
    assert "Failed to download" in result.output
