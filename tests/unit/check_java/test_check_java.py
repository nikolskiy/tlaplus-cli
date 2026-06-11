import pytest

from tlaplus_cli import java
from tlaplus_cli.cli import app


@pytest.mark.parametrize(
    "version_str, expected",
    [
        ("1.8.0_202", 8),
        ("9.0.4", 9),
        ("11.0.2", 11),
        ("17", 17),
        ("21.0.1", 21),
    ],
)
def test_parse_java_version(version_str, expected):
    """Test parsing of Java version strings."""
    assert java.parse_java_version(version_str) == expected


def test_get_java_version_success(mocker):
    """Test successful retrieval of Java version."""
    mock_run = mocker.patch("tlaplus_cli.java.inspector.subprocess.run")
    # Simulate java -version output (it usually goes to stderr)
    mock_run.return_value = mocker.MagicMock(
        stdout="", stderr='openjdk version "11.0.2" 2019-01-15\nOpenJDK Runtime Environment 18.9...'
    )
    mocker.patch("tlaplus_cli.java.inspector.shutil.which", return_value="/usr/bin/java")

    assert java.get_java_version() == "11.0.2"


def test_get_java_version_not_found(mocker):
    """Test when java is not found in PATH."""
    mocker.patch("tlaplus_cli.java.inspector.shutil.which", return_value=None)
    assert java.get_java_version() is None


@pytest.mark.parametrize(
    "java_ver, min_ver",
    [
        ("11.0.2", 11),
        ("11.0.2", 8),
    ],
)
def test_check_java_version_ok(mocker, base_settings, runner, java_ver, min_ver):
    """Test check passes when version is sufficient."""
    settings = base_settings.model_copy(deep=True)
    mocker.patch("tlaplus_cli.java.inspector.get_java_version", return_value=java_ver)
    mocker.patch("tlaplus_cli.cli.load_config", return_value=settings)

    settings.java.min_version = min_ver
    result = runner.invoke(app, ["check-java"])
    assert result.exit_code == 0


def test_check_java_version_too_low(mocker, base_settings, runner):
    """Test check fails when version is too low."""
    settings = base_settings.model_copy(deep=True)
    mocker.patch("tlaplus_cli.java.inspector.get_java_version", return_value="1.8.0_202")
    mocker.patch("tlaplus_cli.cli.load_config", return_value=settings)
    settings.java.min_version = 11

    result = runner.invoke(app, ["check-java"])
    assert result.exit_code == 1


def test_check_java_version_missing(mocker, base_settings, runner):
    """Test check fails when java is missing."""
    settings = base_settings.model_copy(deep=True)
    mocker.patch("tlaplus_cli.java.inspector.get_java_version", return_value=None)
    mocker.patch("tlaplus_cli.cli.load_config", return_value=settings)
    settings.java.min_version = 11

    result = runner.invoke(app, ["check-java"])
    assert result.exit_code == 1
