from tlaplus_cli.cli import app


def test_tlc_version_flag(mocker, capfd, base_settings, tmp_path, runner):
    """Test that 'tla tlc --version' prints the jar path and only the first line of TLC version."""
    mocker.patch("tlaplus_cli.tlc.runner.load_config", return_value=base_settings)

    # Create a fake pinned version dir with a jar
    pinned_dir = (tmp_path / "tools" / "v1.8.0-abcdef1").absolute()
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake jar")
    mocker.patch("tlaplus_cli.tlc.compiler.get_pinned_version_dir", return_value=pinned_dir)

    mock_result = mocker.MagicMock()
    mock_result.stdout = "TLC2 Version Mock\nSome other output"
    mock_result.stderr = ""
    mocker.patch("tlaplus_cli.tlc.runner.subprocess.run", return_value=mock_result)

    result = runner.invoke(app, ["tlc", "--version"])
    assert result.exit_code == 0

    captured = capfd.readouterr()
    stdout = captured.out + result.stdout
    assert f"tla2tools.jar path: {pinned_dir / 'tla2tools.jar'}" in stdout
    assert "TLC2 Version Mock" in stdout
    assert "Some other output" not in stdout
