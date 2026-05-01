from tlaplus_cli.cli import app


def test_modules_path_resolved(mocker, tmp_path, runner, base_settings):
    """Test that tla modules path --resolved shows resolved paths."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    modules_dir = project_dir / "modules"
    modules_dir.mkdir()

    classes_dir = project_dir / "classes"
    classes_dir.mkdir()

    lib_dir = project_dir / "lib"
    lib_dir.mkdir()
    jar = lib_dir / "foo.jar"
    jar.touch()

    tla_jar = tmp_path / "tla2tools.jar"
    tla_jar.touch()

    mocker.patch("tlaplus_cli.cmd.modules.path.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.cmd.modules.path.workspace_root", return_value=project_dir)
    mocker.patch("tlaplus_cli.cmd.modules.path.get_tlc_jar_path", return_value=tla_jar)

    result = runner.invoke(app, ["modules", "path", "--resolved"])
    assert result.exit_code == 0
    assert f"Source Path: {modules_dir}" in result.stdout
    assert f"Classes Path: {classes_dir}" in result.stdout
    assert "Library Path: 1 JARs" in result.stdout
    assert f"- {jar}" in result.stdout
    assert f"Tool Jar: {tla_jar}" in result.stdout
