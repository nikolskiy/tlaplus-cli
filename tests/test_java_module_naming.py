import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tlaplus_cli.cli import app

runner = CliRunner()

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

    mocker.patch("tlaplus_cli.build_tlc_module.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=fixture_dir)
    mocker.patch("tlaplus_cli.run_tlc.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.run_tlc.workspace_root", return_value=fixture_dir)


@pytest.mark.skipif(not JAVA_AVAILABLE, reason="java not found")
@pytest.mark.skipif(not JAVAC_AVAILABLE, reason="javac not found")
def test_tlc_overrides_naming_works(tmp_path, mocker, base_settings, capfd, naming_fixed_dir, monkeypatch):
    """
    Tests that naming the class 'TLCOverrides' in 'tlc2.overrides' package works.
    This is the currently supported approach.
    """
    setup_naming_env(tmp_path, mocker, base_settings, naming_fixed_dir)

    res_build = runner.invoke(app, ["build"])
    assert res_build.exit_code == 0, f"Module compilation failed: {res_build.stdout}"

    monkeypatch.chdir(naming_fixed_dir)
    res_tlc = runner.invoke(app, ["tlc", "test_spec"])
    assert res_tlc.exit_code == 0, f"TLC run failed: {res_tlc.stdout}"

    stdout = capfd.readouterr().out + res_tlc.stdout
    assert "OVERRIDE_ACTIVE_TLCOverrides" in stdout, "TLCOverrides approach should work but failed!"


@pytest.mark.skipif(not JAVA_AVAILABLE, reason="java not found")
@pytest.mark.skipif(not JAVAC_AVAILABLE, reason="javac not found")
def test_module_name_class_naming_fails(tmp_path, mocker, base_settings, capfd, naming_dynamic_dir, monkeypatch):
    """
    Tests that naming the class after the module ('TestModule') fails to load the override.
    According to current TLC behavior, this doesn't work. We want this test to pass
    as long as the behavior remains broken, so we are alerted if/when TLC fixes this.
    """
    setup_naming_env(tmp_path, mocker, base_settings, naming_dynamic_dir)

    res_build = runner.invoke(app, ["build"])
    assert res_build.exit_code == 0, f"Module compilation failed: {res_build.stdout}"

    monkeypatch.chdir(naming_dynamic_dir)
    res_tlc = runner.invoke(app, ["tlc", "test_spec"])
    assert res_tlc.exit_code == 0, f"TLC run failed: {res_tlc.stdout}"

    stdout = capfd.readouterr().out + res_tlc.stdout

    # If this assertion fails, it means TLC updated its underlying library to actually support
    # module-named classes! In that case, we should update our documentation and change this test.
    assert "OVERRIDE_ACTIVE_TestModule" not in stdout, (
        "EXPECTED FAILURE: Naming the class after the module (TestModule.java) actually worked! "
        "TLC behavior has changed. Update docs to reflect this new capability."
    )
