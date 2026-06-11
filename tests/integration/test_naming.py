import pytest

from tlaplus_cli.cli import app
from tlaplus_cli.cmd.tlc import TlcFormatter


@pytest.fixture
def naming_fixed_dir(fixtures_dir):
    return fixtures_dir / "naming_fixed"


@pytest.fixture
def naming_dynamic_dir(fixtures_dir):
    return fixtures_dir / "naming_dynamic"


def test_tlc_overrides_naming_works(
    tmp_path,
    mocker,
    base_settings,
    naming_fixed_dir,
    monkeypatch,
    runner,
    setup_naming_env_fixture,
    java_available,
    javac_available,
    compile_test_modules_fixture,
):
    """
    Tests that naming the class 'TLCOverrides' in 'tlc2.overrides' package works.
    This is the currently supported approach.
    """
    if not java_available:
        pytest.skip("java not found")
    if not javac_available:
        pytest.skip("javac not found")
    setup_naming_env_fixture(tmp_path, mocker, base_settings, naming_fixed_dir)
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    captured_result = None
    original_update_logs = TlcFormatter.update_logs

    def mock_update_logs(self, layout, result):
        nonlocal captured_result
        captured_result = result
        original_update_logs(self, layout, result)

    mocker.patch("tlaplus_cli.cmd.tlc.TlcFormatter.update_logs", mock_update_logs)

    compile_test_modules_fixture(naming_fixed_dir, tmp_path / "classes", base_settings)

    monkeypatch.chdir(naming_fixed_dir)
    res_tlc = runner.invoke(app, ["tlc", "test_spec"])
    assert res_tlc.exit_code == 0, f"TLC run failed: {res_tlc.stdout}"

    assert captured_result is not None
    output_lines_str = "\n".join(captured_result.output_lines)
    assert "OVERRIDE_ACTIVE_TLCOverrides" in output_lines_str, "TLCOverrides approach should work but failed!"


def test_module_name_class_naming_succeeds(
    tmp_path,
    mocker,
    base_settings,
    naming_dynamic_dir,
    monkeypatch,
    runner,
    setup_naming_env_fixture,
    java_available,
    javac_available,
    compile_test_modules_fixture,
):
    """
    Tests that naming the class after the module ('TestModule') succeeds in loading the override.
    This works because the CLI dynamically discovers classes implementing ITLCOverrides.
    """
    if not java_available:
        pytest.skip("java not found")
    if not javac_available:
        pytest.skip("javac not found")
    setup_naming_env_fixture(tmp_path, mocker, base_settings, naming_dynamic_dir)
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    captured_result = None
    original_update_logs = TlcFormatter.update_logs

    def mock_update_logs(self, layout, result):
        nonlocal captured_result
        captured_result = result
        original_update_logs(self, layout, result)

    mocker.patch("tlaplus_cli.cmd.tlc.TlcFormatter.update_logs", mock_update_logs)

    compile_test_modules_fixture(naming_dynamic_dir, tmp_path / "classes", base_settings)

    monkeypatch.chdir(naming_dynamic_dir)
    res_tlc = runner.invoke(app, ["tlc", "test_spec"])
    assert res_tlc.exit_code == 0, f"TLC run failed: {res_tlc.stdout}"

    assert captured_result is not None
    output_lines_str = "\n".join(captured_result.output_lines)

    assert "OVERRIDE_ACTIVE_TestModule" in output_lines_str, (
        "Dynamic class naming (naming the override class TestModule instead of TLCOverrides) failed to load!"
    )
