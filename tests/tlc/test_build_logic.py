from tlaplus_cli.cli import app


def test_build_with_explicit_path(mocker, tmp_path, base_settings, runner):
    """modules build with explicit path uses that path as project root."""
    project_dir = tmp_path / "my_project"
    modules_dir = project_dir / "modules"
    modules_dir.mkdir(parents=True)
    (modules_dir / "Foo.java").write_text("class Foo {}")

    settings = base_settings.model_copy(deep=True)
    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=settings)
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=tmp_path)

    mock_run = mocker.patch("tlaplus_cli.build_tlc_module.subprocess.run")
    mock_run.return_value.returncode = 0

    # Patch jar path to exist
    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake")
    mocker.patch("tlaplus_cli.build_tlc_module.get_pinned_version_dir", return_value=pinned_dir)

    result = runner.invoke(app, ["modules", "build", str(project_dir)])
    assert result.exit_code == 0
    args, _ = mock_run.call_args
    cmd = args[0]
    assert str(project_dir / "classes") in cmd  # -d target
    assert str(modules_dir / "Foo.java") in cmd  # source file


def test_build_without_path_uses_workspace_root(mocker, tmp_path, base_settings, runner):
    """modules build without path uses workspace_root from config."""
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    modules_dir = project_dir / "modules"
    modules_dir.mkdir()
    (modules_dir / "Bar.java").write_text("class Bar {}")

    settings = base_settings.model_copy(deep=True)
    settings.workspace.root = project_dir
    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=settings)
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=project_dir)

    mock_run = mocker.patch("tlaplus_cli.build_tlc_module.subprocess.run")
    mock_run.return_value.returncode = 0

    # Patch jar path to exist
    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake")
    mocker.patch("tlaplus_cli.build_tlc_module.get_pinned_version_dir", return_value=pinned_dir)

    result = runner.invoke(app, ["modules", "build"])
    assert result.exit_code == 0
    args, _ = mock_run.call_args
    cmd = args[0]
    assert str(project_dir / "classes") in cmd
    assert str(modules_dir / "Bar.java") in cmd


def test_build_includes_lib_jars_in_classpath(mocker, tmp_path, base_settings, runner):
    """javac classpath includes *.jar files from project lib/ directory."""
    project_dir = tmp_path / "my_project"
    (project_dir / "modules").mkdir(parents=True)
    (project_dir / "modules" / "Foo.java").write_text("class Foo {}")
    lib_dir = project_dir / "lib"
    lib_dir.mkdir()
    extra_jar = lib_dir / "extra.jar"
    extra_jar.write_bytes(b"fake")

    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    tla_jar = pinned_dir / "tla2tools.jar"
    tla_jar.write_bytes(b"fake")

    settings = base_settings.model_copy(deep=True)
    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=settings)
    mocker.patch("tlaplus_cli.build_tlc_module.get_pinned_version_dir", return_value=pinned_dir)

    mock_run = mocker.patch("tlaplus_cli.build_tlc_module.subprocess.run")
    mock_run.return_value.returncode = 0

    result = runner.invoke(app, ["modules", "build", str(project_dir)])
    assert result.exit_code == 0
    args, _ = mock_run.call_args
    cmd_str = " ".join(args[0])
    assert str(extra_jar) in cmd_str
