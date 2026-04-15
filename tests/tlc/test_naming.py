
import pytest

from tlaplus_cli.cli import app


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
    capfd,
    naming_fixed_dir,
    monkeypatch,
    runner,
    setup_naming_env_fixture,
    java_available,
    javac_available,
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

    res_build = runner.invoke(app, ["modules", "build"])
    assert res_build.exit_code == 0, f"Module compilation failed: {res_build.stdout}"

    monkeypatch.chdir(naming_fixed_dir)
    res_tlc = runner.invoke(app, ["tlc", "test_spec"])
    assert res_tlc.exit_code == 0, f"TLC run failed: {res_tlc.stdout}"

    stdout = capfd.readouterr().out + res_tlc.stdout
    assert "OVERRIDE_ACTIVE_TLCOverrides" in stdout, "TLCOverrides approach should work but failed!"


def test_module_name_class_naming_fails(
    tmp_path,
    mocker,
    base_settings,
    capfd,
    naming_dynamic_dir,
    monkeypatch,
    runner,
    setup_naming_env_fixture,
    java_available,
    javac_available,
):
    """
    Tests that naming the class after the module ('TestModule') fails to load the override.
    According to current TLC behavior, this doesn't work. We want this test to pass
    as long as the behavior remains broken, so we are alerted if/when TLC fixes this.
    """
    if not java_available:
        pytest.skip("java not found")
    if not javac_available:
        pytest.skip("javac not found")
    setup_naming_env_fixture(tmp_path, mocker, base_settings, naming_dynamic_dir)

    res_build = runner.invoke(app, ["modules", "build"])
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
