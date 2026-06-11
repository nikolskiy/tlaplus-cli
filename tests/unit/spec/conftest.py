from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_tlc_env(mocker, tmp_path, base_settings):
    mocker.patch("tlaplus_cli.tlc.runner.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    pinned_dir = (tmp_path / "tools" / "v1.8.0").absolute()
    pinned_dir.mkdir(parents=True)
    (pinned_dir / "tla2tools.jar").write_bytes(b"fake")
    mocker.patch("tlaplus_cli.tlc.compiler.get_pinned_version_dir", return_value=pinned_dir)

    # Patch subprocess.Popen instead of subprocess.run
    mock_popen = mocker.patch("tlaplus_cli.tlc.runner.subprocess.Popen")

    # Configure the mock process
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = iter([])  # Empty iterator for lines
    mock_process.communicate.return_value = ("", "")
    mock_process.__enter__.return_value = mock_process

    mock_popen.return_value = mock_process

    # We also need to mock run_tlc to return success result if needed,
    # or ensure TlcParser.get_result() is available.
    # Actually, the problem is in cmd/tlc.py which calls run_tlc.
    # run_tlc calls subprocess.Popen.
    # If we want run_tlc to succeed from cmd/tlc.py perspective,
    # we might need to mock it directly in some tests,
    # but many tests here expect to check the command line passed to Popen.

    # To make cmd/tlc.py happy, it needs a ModelCheckResult with Success state.
    # But run_tlc processes output to set that state.
    # If we provide "@!@!@success@!@!@" in stdout, the parser will set it.

    success_marker = "@!@!@type:100:0@!@!@@!@!@success@!@!@"
    mock_process.stdout = iter([success_marker])

    return mock_popen
