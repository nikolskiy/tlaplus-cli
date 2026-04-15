from tlaplus_cli.cli import app


def test_tlc_classpath_includes_project_classes(mock_tlc_env, tmp_path, base_settings, runner):
    """When a classes/ directory exists next to the spec, it must appear in the JVM classpath."""
    project_dir = tmp_path / "my_project"
    spec_dir = project_dir
    spec_dir.mkdir(parents=True)
    (spec_dir / "queue.tla").write_text("MODULE queue\n===\n")
    (project_dir / "classes").mkdir()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["tlc", str(spec_dir / "queue.tla")])

    assert result.exit_code == 0
    args, _ = mock_tlc_env.call_args
    cmd = args[0]
    cp_index = cmd.index("-cp")
    classpath = cmd[cp_index + 1]
    assert str(project_dir / "classes") in classpath


def test_tlc_classpath_includes_lib_jars(mock_tlc_env, tmp_path, base_settings, runner):
    """When a lib/ directory with JARs exists, they must appear in the JVM classpath."""
    project_dir = tmp_path / "my_project"
    spec_dir = project_dir / "spec"
    spec_dir.mkdir(parents=True)
    (spec_dir / "queue.tla").write_text("MODULE queue\n===\n")
    lib_dir = project_dir / "lib"
    lib_dir.mkdir()
    extra_jar = lib_dir / "extra.jar"
    extra_jar.write_bytes(b"fake")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["tlc", str(spec_dir / "queue.tla")])

    assert result.exit_code == 0
    args, _ = mock_tlc_env.call_args
    cmd = args[0]
    cp_index = cmd.index("-cp")
    classpath = cmd[cp_index + 1]
    assert str(extra_jar) in classpath


def test_tlc_tla_library_set_when_modules_dir_exists(mock_tlc_env, tmp_path, base_settings, runner):
    """-DTLA-Library is set when a modules/ directory is found."""
    project_dir = tmp_path / "my_project"
    spec_dir = project_dir / "tests"
    spec_dir.mkdir(parents=True)
    (spec_dir / "queue_test.tla").write_text("MODULE queue_test\n===\n")
    modules_dir = project_dir / "modules"
    modules_dir.mkdir()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["tlc", str(spec_dir / "queue_test.tla")])

    assert result.exit_code == 0
    args, _ = mock_tlc_env.call_args
    cmd = args[0]
    assert f"-DTLA-Library={modules_dir}" in cmd


def test_tlc_no_project_dirs_no_extra_classpath(mock_tlc_env, tmp_path, base_settings, runner):
    """A spec without adjacent project dirs has no extra classpath entries."""
    spec_dir = tmp_path / "standalone"
    spec_dir.mkdir()
    (spec_dir / "simple.tla").write_text("MODULE simple\n===\n")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["tlc", str(spec_dir / "simple.tla")])

    assert result.exit_code == 0
    args, _ = mock_tlc_env.call_args
    cmd = args[0]
    cp_index = cmd.index("-cp")
    classpath = cmd[cp_index + 1]
    # Should only contain the tla2tools.jar
    assert "tla2tools.jar" in classpath
    assert "classes" not in classpath
    assert "lib" not in classpath
