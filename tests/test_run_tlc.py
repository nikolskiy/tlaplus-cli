import shutil

import pytest
import typer

from tla import build_tlc_module, run_tlc

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
def test_run_tlc_integration(mocker, tmp_path, capfd, queue_dir, base_settings):
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

    mocker.patch("tla.run_tlc.load_config", return_value=base_settings)
    mocker.patch("tla.run_tlc.workspace_root", return_value=queue_dir)

    # We also need to patch build_tlc_module's config loading to compile first
    mocker.patch("tla.build_tlc_module.load_config", return_value=base_settings)
    # Patch workspace_root for build_tlc_module
    mocker.patch("tla.build_tlc_module.workspace_root", return_value=queue_dir)

    # 1. Compile modules
    try:
        build_tlc_module.build(verbose=False)
    except (SystemExit, typer.Exit) as e:
        code = e.code if isinstance(e, SystemExit) else e.exit_code
        assert code == 0, "Module compilation failed"

    # 2. Run TLC
    # Verify that classes_dir is populated
    assert (classes_dir / "tlc2/overrides/TLCOverrides.class").exists()

    # Run TLC on "queue" spec
    try:
        run_tlc.tlc("queue")
    except SystemExit as e:
        # TLC returns 0 on success (no violations)
        assert e.code == 0, "TLC run failed"
    except typer.Exit as e:
        assert e.exit_code == 0, "TLC run failed"

    # 3. Verify output
    captured = capfd.readouterr()
    stdout = captured.out

    assert "Running TLC on queue.tla" in stdout
    # The output might vary but we expect some successes
    # Note: tlc2tools might print to stderr or stdout depending on version/config
    # We combine them or check both if needed, but usually it's stdout.
    # Let's check for the module override log explicitly.
    assert "State log test:" in stdout
