from tlaplus_cli.cli import app


def test_build_uses_both_local_and_custom_module_path(mocker, tmp_path, base_settings, runner):
    custom_modules = tmp_path / "custom_modules"
    custom_modules.mkdir()
    (custom_modules / "Custom.java").write_text("class Custom {}")

    local_modules = tmp_path / "modules"
    local_modules.mkdir()
    (local_modules / "Local.java").write_text("class Local {}")

    settings = base_settings.model_copy(deep=True)
    settings.module_path = str(custom_modules)
    mocker.patch("tlaplus_cli.tlc.compiler.load_config", return_value=settings)
    mocker.patch("tlaplus_cli.tlc.compiler.workspace_root", return_value=tmp_path)

    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake")
    mocker.patch("tlaplus_cli.tlc.compiler.get_pinned_version_dir", return_value=pinned_dir)

    mock_run = mocker.patch("tlaplus_cli.tlc.compiler.subprocess.run")
    mock_run.return_value.returncode = 0

    result = runner.invoke(app, ["modules", "build"])

    assert result.exit_code == 0
    args, _ = mock_run.call_args
    cmd = args[0]
    assert str(custom_modules / "Custom.java") in cmd
    assert str(local_modules / "Local.java") in cmd
