from unittest.mock import MagicMock

from typer.testing import CliRunner

from tlaplus_cli import check_java
from tlaplus_cli.cli import app

runner = CliRunner()


def test_parse_java_version():
    """Test parsing of Java version strings."""
    assert check_java.parse_java_version("1.8.0_202") == 8
    assert check_java.parse_java_version("9.0.4") == 9
    assert check_java.parse_java_version("11.0.2") == 11
    assert check_java.parse_java_version("17") == 17
    assert check_java.parse_java_version("21.0.1") == 21


def test_get_java_version_success(mocker):
    """Test successful retrieval of Java version."""
    mock_run = mocker.patch("subprocess.run")
    # Simulate java -version output (it usually goes to stderr)
    mock_run.return_value = MagicMock(
        stdout="", stderr='openjdk version "11.0.2" 2019-01-15\nOpenJDK Runtime Environment 18.9...'
    )
    mocker.patch("shutil.which", return_value="/usr/bin/java")

    assert check_java.get_java_version() == "11.0.2"


def test_get_java_version_not_found(mocker):
    """Test when java is not found in PATH."""
    mocker.patch("shutil.which", return_value=None)
    assert check_java.get_java_version() is None


def test_check_java_version_ok(mocker, base_settings):
    """Test check passes when version is sufficient."""
    mocker.patch("tlaplus_cli.check_java.get_java_version", return_value="11.0.2")
    mocker.patch("tlaplus_cli.cli.load_config", return_value=base_settings)

    base_settings.java.min_version = 11
    result = runner.invoke(app, ["check-java"])
    assert result.exit_code == 0

    base_settings.java.min_version = 8
    result = runner.invoke(app, ["check-java"])
    assert result.exit_code == 0


def test_check_java_version_too_low(mocker, base_settings):
    """Test check fails when version is too low."""
    mocker.patch("tlaplus_cli.check_java.get_java_version", return_value="1.8.0_202")
    mocker.patch("tlaplus_cli.cli.load_config", return_value=base_settings)
    base_settings.java.min_version = 11

    result = runner.invoke(app, ["check-java"])
    assert result.exit_code == 1


def test_check_java_version_missing(mocker, base_settings):
    """Test check fails when java is missing."""
    mocker.patch("tlaplus_cli.check_java.get_java_version", return_value=None)
    mocker.patch("tlaplus_cli.cli.load_config", return_value=base_settings)
    base_settings.java.min_version = 11

    result = runner.invoke(app, ["check-java"])
    assert result.exit_code == 1
