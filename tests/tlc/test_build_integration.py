import pytest

from tlaplus_cli.cli import app


def test_build_integration(mocker, tmp_path, queue_dir, base_settings, runner, javac_available):
    """
    Integration test for build_tlc_module.build().
    Uses the actual files in tla-example and the real tla2tools.jar (if available).
    Verified output classes are generated in a temporary directory.
    """
    if not javac_available:
        pytest.skip("javac not found")

    # Create a temporary classes directory
    classes_dir = tmp_path / "classes"

    # Configure base_settings for this test
    settings = base_settings.model_copy(deep=True)
    settings.workspace.root = queue_dir
    settings.workspace.classes_dir = str(classes_dir)

    # Patch load_config to return our mock config
    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=settings)

    # Patch workspace_root to return the example directory
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=queue_dir)

    # Run build
    result = runner.invoke(app, ["modules", "build", "--verbose"])
    assert result.exit_code == 0, f"Build failed with {result.exit_code}: {result.stdout}"

    # Verify outputs
    assert classes_dir.exists(), "Classes directory not created"

    # Verify TLCOverrides.class exists
    output_class = classes_dir / "tlc2/overrides/TLCOverrides.class"
    assert output_class.exists(), f"Class file not found at {output_class}"

    # Verify META-INF service file
    service_file = classes_dir / "META-INF/services/tlc2.overrides.ITLCOverrides"
    assert service_file.exists(), "Service file not found"

    content = service_file.read_text().strip()
    assert content == "tlc2.overrides.TLCOverrides", f"Unexpected service file content: {content}"


def test_build_custom_overrides(mocker, tmp_path, queue_dir, base_settings, runner, javac_available):
    """
    Test build with custom overrides class configuration.
    """
    if not javac_available:
        pytest.skip("javac not found")

    classes_dir = tmp_path / "classes"

    # Configure custom override
    settings = base_settings.model_copy(deep=True)
    custom_override = "com.example.MyOverrides"
    settings.tlc.overrides_class = custom_override
    settings.workspace.root = queue_dir
    settings.workspace.classes_dir = str(classes_dir)

    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=settings)
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=queue_dir)

    result = runner.invoke(app, ["modules", "build"])
    assert result.exit_code == 0, f"Build failed: {result.stdout}"

    service_file = classes_dir / "META-INF/services/tlc2.overrides.ITLCOverrides"
    assert service_file.exists()
    assert service_file.read_text().strip() == custom_override
