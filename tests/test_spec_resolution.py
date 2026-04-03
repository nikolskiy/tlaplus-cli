from pathlib import Path

import pytest
from typer.testing import CliRunner

from tlaplus_cli.cli import app

runner = CliRunner()


@pytest.fixture
def mock_tlc_env(mocker, tmp_path, base_settings):
    mocker.patch("tlaplus_cli.run_tlc.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.run_tlc.workspace_root", return_value=tmp_path)
    mocker.patch("tlaplus_cli.run_tlc.check_java_version")

    pinned_dir = (tmp_path / "tools" / "v1.8.0").absolute()
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake")
    mocker.patch("tlaplus_cli.run_tlc.get_pinned_version_dir", return_value=pinned_dir)

    mock_run = mocker.patch("tlaplus_cli.run_tlc.subprocess.run")
    mock_run.return_value.returncode = 0
    return mock_run


def test_scenario_1_explicit_extension(mock_tlc_env, tmp_path):
    """Scenario 1: Model with explicit .tla extension in CWD."""
    spec_name = "my_model.tla"
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(spec_name).write_text("MODULE my_model\n===\n")
        result = runner.invoke(app, ["tlc", spec_name])

    assert result.exit_code == 0
    args, _ = mock_tlc_env.call_args
    assert "my_model.tla" in args[0]


def test_scenario_2_missing_extension_cwd(mock_tlc_env, tmp_path):
    """Scenario 2: Model with missing .tla extension in CWD."""
    spec_name = "my_model"
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(f"{spec_name}.tla").write_text("MODULE my_model\n===\n")
        result = runner.invoke(app, ["tlc", spec_name])

    assert result.exit_code == 0
    args, _ = mock_tlc_env.call_args
    assert "my_model.tla" in args[0]


def test_scenario_3_inside_spec_directory_cwd(mock_tlc_env, tmp_path):
    """Scenario 3: Model inside a spec/ subdirectory in CWD."""
    spec_name = "my_model"
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("spec").mkdir()
        Path("spec/my_model.tla").write_text("MODULE my_model\n===\n")
        result = runner.invoke(app, ["tlc", spec_name])

    assert result.exit_code == 0
    args, _ = mock_tlc_env.call_args
    assert "my_model.tla" in args[0]


def test_scenario_4_spec_not_found_cwd(mock_tlc_env, tmp_path):
    """Scenario 4: Spec not found in CWD (validate multiline error)."""
    spec_name = "missing_model"
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["tlc", spec_name])

    assert result.exit_code == 1
    assert "Error: Could not find a TLA+ spec file. Looked in the following locations:" in result.output
    assert f"- {spec_name}" in result.output
    assert f"- {spec_name}.tla" in result.output
    assert f"- spec/{spec_name}.tla" in result.output


def test_scenario_5_missing_extension_path(mock_tlc_env, tmp_path):
    """Scenario 5: Spec missing .tla extension, but inside a specified path."""
    spec_path = "subdir/my_model"
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("subdir").mkdir()
        Path("subdir/my_model.tla").write_text("MODULE my_model\n===\n")
        result = runner.invoke(app, ["tlc", spec_path])

    assert result.exit_code == 0
    args, _ = mock_tlc_env.call_args
    assert "my_model.tla" in args[0]


def test_scenario_6_inside_spec_directory_path(mock_tlc_env, tmp_path):
    """Scenario 6: Spec inside a spec/ subdirectory within a specified path."""
    spec_path = "subdir/my_model"
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("subdir/spec").mkdir(parents=True)
        Path("subdir/spec/my_model.tla").write_text("MODULE my_model\n===\n")
        result = runner.invoke(app, ["tlc", spec_path])

    assert result.exit_code == 0
    args, _ = mock_tlc_env.call_args
    assert "my_model.tla" in args[0]


def test_scenario_7_spec_not_found_path(mock_tlc_env, tmp_path):
    """Scenario 7: Spec not found with a path (validate exactly where it looked)."""
    spec_path = "subdir/missing_model"
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("subdir").mkdir()
        result = runner.invoke(app, ["tlc", spec_path])

    assert result.exit_code == 1
    assert "Error: Could not find a TLA+ spec file. Looked in the following locations:" in result.output
    assert f"- {spec_path}" in result.output
    assert f"- {spec_path}.tla" in result.output
    assert "- subdir/spec/missing_model.tla" in result.output
