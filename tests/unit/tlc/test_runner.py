from unittest.mock import MagicMock

from tlaplus_cli.tlc.runner import run_tlc


def test_run_tlc_keyboard_interrupt(mocker):
    """Test that run_tlc handles KeyboardInterrupt gracefully."""
    # Mock subprocess.Popen
    mock_process = MagicMock()
    # Popen used as context manager returns the process object from __enter__
    mock_process.__enter__.return_value = mock_process
    mock_process.stdout = ["line 1\n", "line 2\n"]
    mock_process.returncode = 0

    # We want to raise KeyboardInterrupt during iteration
    def side_effect():
        yield "line 1\n"
        raise KeyboardInterrupt()

    mock_process.stdout = side_effect()

    mocker.patch("subprocess.Popen", return_value=mock_process)
    mocker.patch("tlaplus_cli.tlc.runner.load_config")
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")
    mocker.patch("tlaplus_cli.tlc.runner.resolve_spec_file", return_value=(MagicMock(), "Spec"))
    mocker.patch("tlaplus_cli.tlc.runner.build_tlc_command", return_value=["java", "tlc2.TLC", "Spec"])

    callback = MagicMock()

    # We expect run_tlc to catch KeyboardInterrupt and return exit code
    exit_code = run_tlc("Spec", callback=callback)

    assert exit_code == 0
    mock_process.terminate.assert_called_once()
    # It should have called callback at least once before interrupt
    assert callback.called
