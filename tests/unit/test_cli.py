import pytest
import typer

from tlaplus_cli.cli import app, version_callback


def test_version_callback_exits(mocker):
    """Test version callback exits after printing."""
    mock_metadata = mocker.patch("importlib.metadata.metadata")
    mock_metadata.return_value = {
        "Name": "tlaplus-cli",
        "Version": "1.2.3",
        "Summary": "Test summary",
    }

    with pytest.raises(typer.Exit):
        version_callback(True)

    mock_metadata.assert_called_once_with("tlaplus-cli")


def test_cli_version_flag(mocker, runner):
    """Test 'tla --version' command."""
    mock_metadata = mocker.patch("importlib.metadata.metadata")
    mock_metadata.return_value = {
        "Name": "tlaplus-cli",
        "Version": "1.2.3",
        "Summary": "Test summary",
    }
    mocker.patch("tlaplus_cli.cli.get_app_version", return_value="1.2.3")

    # Running the CLI with --version
    result = runner.invoke(app, ["--version"])

    # It should exit with 0
    assert result.exit_code == 0
    assert "tlaplus-cli v1.2.3" in result.stdout
    assert "Test summary" in result.stdout

    mock_metadata.assert_called_once_with("tlaplus-cli")


def test_cli_version_flag_dev_commit(mocker, runner):
    """Test 'tla --version' command in dev installation mode with commit hash."""
    mock_metadata = mocker.patch("importlib.metadata.metadata")
    mock_metadata.return_value = {
        "Name": "tlaplus-cli",
        "Version": "1.2.3",
        "Summary": "Test summary",
    }
    mocker.patch("tlaplus_cli.cli.get_app_version", return_value="1.2.3+754bd16")

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "tlaplus-cli v1.2.3+754bd16" in result.stdout
    assert "Test summary" in result.stdout

