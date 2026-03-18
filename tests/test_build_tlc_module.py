import shutil

import pytest
from typer.testing import CliRunner

from tlaplus_cli.cli import app

runner = CliRunner()

# Define paths relative to the test file
# Check if javac is available
JAVAC_AVAILABLE = shutil.which("javac") is not None


@pytest.mark.skipif(not JAVAC_AVAILABLE, reason="javac not found")
def test_build_integration(mocker, tmp_path, queue_dir, base_settings):
    """
    Integration test for build_tlc_module.build().
    Uses the actual files in tla-example and the real tla2tools.jar (if available).
    Verified output classes are generated in a temporary directory.
    """
    # Create a temporary classes directory
    classes_dir = tmp_path / "classes"

    # Configure base_settings for this test
    base_settings.workspace.root = queue_dir
    base_settings.workspace.classes_dir = classes_dir

    # Patch load_config to return our mock config
    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=base_settings)

    # Patch workspace_root to return the example directory
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=queue_dir)

    # Run build
    result = runner.invoke(app, ["build", "--verbose"])
    assert result.exit_code == 0, f"Build failed with {result.exit_code}: {result.stdout}"

    # Verify outputs
    assert classes_dir.exists(), "Classes directory not created"

    # Verify TLCOverrides.class exists
    # The source is modules/tlc2/overrides/TLCOverrides.java
    # Package is tlc2.overrides, so output should be in tlc2/overrides/
    output_class = classes_dir / "tlc2/overrides/TLCOverrides.class"
    assert output_class.exists(), f"Class file not found at {output_class}"

    # Verify META-INF service file
    service_file = classes_dir / "META-INF/services/tlc2.overrides.ITLCOverrides"
    assert service_file.exists(), "Service file not found"

    content = service_file.read_text().strip()
    assert content == "tlc2.overrides.TLCOverrides", f"Unexpected service file content: {content}"


@pytest.mark.skipif(not JAVAC_AVAILABLE, reason="javac not found")
def test_build_custom_overrides(mocker, tmp_path, queue_dir, base_settings):
    """
    Test build with custom overrides class configuration.
    """
    classes_dir = tmp_path / "classes"

    # Configure custom override
    custom_override = "com.example.MyOverrides"
    base_settings.tlc.overrides_class = custom_override
    base_settings.workspace.root = queue_dir
    base_settings.workspace.classes_dir = classes_dir

    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=queue_dir)

    result = runner.invoke(app, ["build"])
    assert result.exit_code == 0, f"Build failed: {result.stdout}"

    service_file = classes_dir / "META-INF/services/tlc2.overrides.ITLCOverrides"
    assert service_file.exists()
    assert service_file.read_text().strip() == custom_override
