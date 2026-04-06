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
    result = runner.invoke(app, ["modules", "build", "--verbose"])
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

    result = runner.invoke(app, ["modules", "build"])
    assert result.exit_code == 0, f"Build failed: {result.stdout}"

    service_file = classes_dir / "META-INF/services/tlc2.overrides.ITLCOverrides"
    assert service_file.exists()
    assert service_file.read_text().strip() == custom_override


def test_build_with_explicit_path(mocker, tmp_path, base_settings):
    """modules build with explicit path uses that path as project root."""
    project_dir = tmp_path / "my_project"
    modules_dir = project_dir / "modules"
    modules_dir.mkdir(parents=True)
    (modules_dir / "Foo.java").write_text("class Foo {}")

    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=base_settings)
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


def test_build_without_path_uses_workspace_root(mocker, tmp_path, base_settings):
    """modules build without path uses workspace_root from config."""
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    modules_dir = project_dir / "modules"
    modules_dir.mkdir()
    (modules_dir / "Bar.java").write_text("class Bar {}")

    base_settings.workspace.root = project_dir
    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=base_settings)
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


def test_build_includes_lib_jars_in_classpath(mocker, tmp_path, base_settings):
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

    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.build_tlc_module.get_pinned_version_dir", return_value=pinned_dir)

    mock_run = mocker.patch("tlaplus_cli.build_tlc_module.subprocess.run")
    mock_run.return_value.returncode = 0

    result = runner.invoke(app, ["modules", "build", str(project_dir)])
    assert result.exit_code == 0
    args, _ = mock_run.call_args
    cmd_str = " ".join(args[0])
    assert str(extra_jar) in cmd_str
