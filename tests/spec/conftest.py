import pytest


@pytest.fixture
def mock_tlc_env(mocker, tmp_path, base_settings):
    mocker.patch("tlaplus_cli.tlc.runner.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    pinned_dir = (tmp_path / "tools" / "v1.8.0").absolute()
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake")
    mocker.patch("tlaplus_cli.tlc.compiler.get_pinned_version_dir", return_value=pinned_dir)

    mock_run = mocker.patch("tlaplus_cli.tlc.runner.subprocess.run")
    mock_run.return_value.returncode = 0
    return mock_run
