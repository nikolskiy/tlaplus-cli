from tlaplus_cli.cli import app


def test_modules_build_show_command(mocker, tmp_path, runner, base_settings):
    """Test that tla modules build --show-command prints the javac command."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    modules_dir = project_dir / "modules"
    modules_dir.mkdir()
    (modules_dir / "Test.java").touch()

    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    tla_jar = pinned_dir / "tla2tools.jar"
    tla_jar.touch()

    mocker.patch("tlaplus_cli.tlc.compiler.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.tlc.compiler.get_pinned_version_dir", return_value=pinned_dir)
    mocker.patch("tlaplus_cli.tlc.compiler.workspace_root", return_value=project_dir)

    result = runner.invoke(app, ["modules", "build", str(project_dir), "--show-command"])
    assert result.exit_code == 0
    assert "javac" in result.stdout
    assert "-cp" in result.stdout
    assert str(tla_jar) in result.stdout
    assert str(project_dir / "classes") in result.stdout
    assert str(modules_dir / "Test.java") in result.stdout
