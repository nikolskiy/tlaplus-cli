from tlaplus_cli.cli import app


def test_build_uses_configured_module_path(mocker, tmp_path, base_settings, runner):
    """Test that build uses module_path from config if available."""
    # Custom module path
    custom_modules = tmp_path / "custom_modules"
    custom_modules.mkdir()
    (custom_modules / "MyModule.java").write_text("class MyModule {}")

    # Update settings
    settings = base_settings.model_copy(deep=True)
    settings.module_path = str(custom_modules)
    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=settings)

    # Mock subprocess.run
    mock_run = mocker.patch("tlaplus_cli.build_tlc_module.subprocess.run")
    mock_run.return_value.returncode = 0

    # Mock jar path
    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake")
    mocker.patch("tlaplus_cli.build_tlc_module.get_pinned_version_dir", return_value=pinned_dir)

    result = runner.invoke(app, ["modules", "build"])

    assert result.exit_code == 0
    args, _ = mock_run.call_args
    cmd = args[0]
    # Source file should be from custom_modules
    assert str(custom_modules / "MyModule.java") in cmd


def test_build_fails_if_module_path_missing(mocker, tmp_path, base_settings, runner):
    """Test that build fails if the configured module_path does not exist."""
    settings = base_settings.model_copy(deep=True)
    settings.module_path = str(tmp_path / "non_existent")
    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=settings)

    # Mock jar path
    pinned_dir = tmp_path / "tools" / "v1.8.0"
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake")
    mocker.patch("tlaplus_cli.build_tlc_module.get_pinned_version_dir", return_value=pinned_dir)

    result = runner.invoke(app, ["modules", "build"])

    assert result.exit_code == 1
    assert "Error: modules directory not found" in result.output
