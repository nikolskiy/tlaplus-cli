import shutil

import pytest
from typer.testing import CliRunner

from tlaplus_cli.cli import app

runner = CliRunner()

# Define paths relative to the test file
# Check if java is available
JAVA_AVAILABLE = shutil.which("java") is not None
JAVAC_AVAILABLE = shutil.which("javac") is not None


@pytest.fixture(scope="module")
def compiled_modules(tmp_path_factory):
    """
    Compiles the queue modules to a temporary directory.
    Returns the path to the classes directory.
    """
    if not JAVAC_AVAILABLE:
        pytest.skip("javac not found")

    return tmp_path_factory.mktemp("classes")


@pytest.mark.skipif(not JAVA_AVAILABLE, reason="java not found")
@pytest.mark.skipif(not JAVAC_AVAILABLE, reason="javac not found")
def test_tlc_integration(mocker, tmp_path, capfd, queue_dir, base_settings, monkeypatch):
    """
    Integration test for run_tlc.tlc().
    1. Compiles the modules (prerequisite).
    2. Runs TLC on queue.tla.
    3. Verifies output.
    """
    classes_dir = tmp_path / "classes"

    # Configure base_settings
    base_settings.workspace.root = queue_dir
    base_settings.workspace.classes_dir = classes_dir

    mocker.patch("tlaplus_cli.run_tlc.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.run_tlc.workspace_root", return_value=queue_dir)

    # We also need to patch build_tlc_module's config loading to compile first
    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=base_settings)
    # Patch workspace_root for build_tlc_module
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=queue_dir)

    # 1. Compile modules
    res_build = runner.invoke(app, ["build"])
    assert res_build.exit_code == 0, f"Module compilation failed: {res_build.stdout}"

    # 2. Run TLC
    # Verify that classes_dir is populated
    assert (classes_dir / "tlc2/overrides/TLCOverrides.class").exists()

    # Run TLC on "queue" spec
    monkeypatch.chdir(queue_dir)
    res_tlc = runner.invoke(app, ["tlc", "queue"])
    assert res_tlc.exit_code == 0, f"TLC run failed: {res_tlc.stdout}"

    # 3. Verify output
    captured = capfd.readouterr()
    stdout = captured.out + res_tlc.stdout

    assert "Running TLC on queue.tla" in stdout
    # The output might vary but we expect some successes
    # Note: tlc2tools might print to stderr or stdout depending on version/config
    # We combine them or check both if needed, but usually it's stdout.
    # Let's check for the module override log explicitly.
    assert "State log test:" in stdout


def test_tlc_version_flag(mocker, capfd, base_settings, tmp_path):
    """Test that 'tla tlc --version' prints the jar path and only the first line of TLC version."""
    mocker.patch("tlaplus_cli.run_tlc.load_config", return_value=base_settings)

    # Create a fake pinned version dir with a jar
    pinned_dir = (tmp_path / "tools" / "v1.8.0-abcdef1").absolute()
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake jar")
    mocker.patch("tlaplus_cli.run_tlc.get_pinned_version_dir", return_value=pinned_dir)

    mock_result = mocker.MagicMock()
    mock_result.stdout = "TLC2 Version Mock\nSome other output"
    mock_result.stderr = ""
    mocker.patch("tlaplus_cli.run_tlc.subprocess.run", return_value=mock_result)

    result = runner.invoke(app, ["tlc", "--version"])
    assert result.exit_code == 0

    captured = capfd.readouterr()
    stdout = captured.out + result.stdout
    assert f"tla2tools.jar path: {pinned_dir / 'tla2tools.jar'}" in stdout
    assert "TLC2 Version Mock" in stdout
    assert "Some other output" not in stdout
