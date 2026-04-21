from tlaplus_cli.cli import app


def test_tlc_uses_custom_module_path(mocker, tmp_path, base_settings, runner):
    """Test that tlc uses module_path for classpath and TLA-Library."""
    # Custom module path
    custom_modules = tmp_path / "custom_modules"
    custom_modules.mkdir()

    # Update settings
    settings = base_settings.model_copy(deep=True)
    settings.module_path = str(custom_modules)
    mocker.patch("tlaplus_cli.tlc.runner.load_config", return_value=settings)

    # Mock jar path
    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake")
    mocker.patch("tlaplus_cli.tlc.compiler.get_pinned_version_dir", return_value=pinned_dir)

    # Create a dummy spec
    spec_file = tmp_path / "MySpec.tla"
    spec_file.write_text("---- MODULE MySpec ----\n====\n")

    # Mock subprocess.run
    mock_run = mocker.patch("tlaplus_cli.tlc.runner.subprocess.run")
    mock_run.return_value.returncode = 0

    # Mock validate_java_version to avoid potential Mock issues
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    result = runner.invoke(app, ["tlc", str(spec_file)])

    assert result.exit_code == 0
    args, _kwargs = mock_run.call_args
    cmd = args[0]
    cmd_str = " ".join(cmd)

    # Phase 4: append the custom directory path to the Java -cp mechanism
    assert str(custom_modules) in cmd_str

    # It should also probably be in TLA-Library
    assert f"-DTLA-Library={custom_modules}" in cmd_str
