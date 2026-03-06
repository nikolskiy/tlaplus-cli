import shutil
from pathlib import Path

import pytest
import typer

from tla import build_tlc_module, run_tlc

JAVA_AVAILABLE = shutil.which("java") is not None
JAVAC_AVAILABLE = shutil.which("javac") is not None

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def naming_fixed_dir():
    return FIXTURES_DIR / "naming_fixed"


@pytest.fixture
def naming_dynamic_dir():
    return FIXTURES_DIR / "naming_dynamic"


def setup_naming_env(tmp_path, mocker, base_settings, fixture_dir):
    """Configures the mocks and settings for testing Java overrides from a fixture dir."""
    classes_dir = tmp_path / "classes"
    classes_dir.mkdir(parents=True, exist_ok=True)

    base_settings.workspace.root = fixture_dir
    base_settings.workspace.modules_dir = "modules"
    base_settings.workspace.spec_dir = "spec"
    base_settings.workspace.classes_dir = str(classes_dir)

    mocker.patch("tla.build_tlc_module.load_config", return_value=base_settings)
    mocker.patch("tla.build_tlc_module.workspace_root", return_value=fixture_dir)
    mocker.patch("tla.run_tlc.load_config", return_value=base_settings)
    mocker.patch("tla.run_tlc.workspace_root", return_value=fixture_dir)


@pytest.mark.skipif(not JAVA_AVAILABLE, reason="java not found")
@pytest.mark.skipif(not JAVAC_AVAILABLE, reason="javac not found")
def test_tlc_overrides_naming_works(tmp_path, mocker, base_settings, capfd, naming_fixed_dir):
    """
    Tests that naming the class 'TLCOverrides' in 'tlc2.overrides' package works.
    This is the currently supported approach.
    """
    setup_naming_env(tmp_path, mocker, base_settings, naming_fixed_dir)

    try:
        build_tlc_module.build(verbose=False)
        run_tlc.tlc("test_spec")
    except (SystemExit, typer.Exit) as e:
        code = e.code if isinstance(e, SystemExit) else e.exit_code
        assert code == 0, "TLC run failed"

    stdout = capfd.readouterr().out
    assert "OVERRIDE_ACTIVE_TLCOverrides" in stdout, "TLCOverrides approach should work but failed!"


@pytest.mark.skipif(not JAVA_AVAILABLE, reason="java not found")
@pytest.mark.skipif(not JAVAC_AVAILABLE, reason="javac not found")
def test_module_name_class_naming_fails(tmp_path, mocker, base_settings, capfd, naming_dynamic_dir):
    """
    Tests that naming the class after the module ('TestModule') fails to load the override.
    According to current TLC behavior, this doesn't work. We want this test to pass
    as long as the behavior remains broken, so we are alerted if/when TLC fixes this.
    """
    setup_naming_env(tmp_path, mocker, base_settings, naming_dynamic_dir)

    try:
        build_tlc_module.build(verbose=False)
        run_tlc.tlc("test_spec")
    except (SystemExit, typer.Exit):
        pass

    stdout = capfd.readouterr().out

    # If this assertion fails, it means TLC updated its underlying library to actually support
    # module-named classes! In that case, we should update our documentation and change this test.
    assert "OVERRIDE_ACTIVE_TestModule" not in stdout, (
        "EXPECTED FAILURE: Naming the class after the module (TestModule.java) actually worked! "
        "TLC behavior has changed. Update docs to reflect this new capability."
    )
