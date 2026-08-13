from tlaplus_cli.cli import app


def test_tlc_show_command(mocker, tmp_path, runner, base_settings):
    """Test that tla tlc --show-command prints the java command."""
    spec_dir = tmp_path / "project"
    spec_dir.mkdir()
    (spec_dir / "Test.tla").write_text("MODULE Test\n===\n")

    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    tla_jar = pinned_dir / "tla2tools.jar"
    tla_jar.touch()

    mocker.patch("tlaplus_cli.tlc.runner.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.tlc.runner.get_tlc_jar_path", return_value=tla_jar)
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    result = runner.invoke(app, ["tlc", str(spec_dir / "Test.tla"), "--show-command"])
    assert result.exit_code == 0
    assert "java" in result.stdout
    assert "-cp" in result.stdout
    assert str(tla_jar) in result.stdout
    assert "tlc2.TLC" in result.stdout
    assert "Test.tla" in result.stdout


def test_tlc_show_command_with_cfg(mocker, tmp_path, runner, base_settings):
    """Test tla tlc --show-command with --cfg flag."""
    spec_dir = tmp_path / "project"
    spec_dir.mkdir()
    (spec_dir / "Test.tla").write_text("MODULE Test\n===\n")
    (spec_dir / "TestVariant.cfg").write_text("SPECIFICATION Spec\n")

    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    tla_jar = pinned_dir / "tla2tools.jar"
    tla_jar.touch()

    mocker.patch("tlaplus_cli.tlc.runner.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.tlc.runner.get_tlc_jar_path", return_value=tla_jar)
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    result = runner.invoke(app, ["tlc", str(spec_dir / "Test.tla"), "--cfg", "TestVariant", "--show-command"])
    assert result.exit_code == 0
    assert "-config" in result.stdout
    assert "TestVariant.cfg" in result.stdout


def test_tlc_with_missing_cfg(mocker, tmp_path, runner, base_settings):
    """Test tla tlc fails cleanly when specified --cfg file is missing."""
    spec_dir = tmp_path / "project"
    spec_dir.mkdir()
    (spec_dir / "Test.tla").write_text("MODULE Test\n===\n")

    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    tla_jar = pinned_dir / "tla2tools.jar"
    tla_jar.touch()

    mocker.patch("tlaplus_cli.tlc.runner.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.tlc.runner.get_tlc_jar_path", return_value=tla_jar)
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    result = runner.invoke(app, ["tlc", str(spec_dir / "Test.tla"), "--cfg", "NonExistentVariant"])
    assert result.exit_code == 1
    assert "Error:" in result.output or "Could not find" in result.output

