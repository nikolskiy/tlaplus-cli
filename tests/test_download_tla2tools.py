from unittest.mock import MagicMock

import pytest
import requests
import typer

from tla import download_tla2tools


@pytest.fixture
def mock_config(mocker, tmp_path, base_settings):
    """Mock configuration."""
    cache_dir = tmp_path / "cache"
    # cache_dir.mkdir() # Removed because config.py logic changed?
    # No, cache_dir might be created by caller, but download_tla2tools creates PARENT.
    # The original test created it. Let's keep creating it if needed, or rely on download() creating parents.
    # download() does jar_path.parent.mkdir(parents=True).
    # If cache_dir is the parent, then it should be fine if it doesn't exist.
    # But let's keep mkdir just in case tests rely on it existing.
    cache_dir.mkdir()

    mocker.patch("tla.download_tla2tools.load_config", return_value=base_settings)
    mocker.patch("tla.download_tla2tools.cache_dir", return_value=cache_dir)
    return base_settings, cache_dir


@pytest.fixture
def mock_requests(mocker):
    """Mock requests.get."""
    return mocker.patch("requests.get")


@pytest.fixture
def mock_check_java(mocker):
    """Mock check_java_version."""
    return mocker.patch("tla.download_tla2tools.check_java_version")


@pytest.fixture
def mock_get_version(mocker):
    """Mock _get_version."""
    return mocker.patch("tla.download_tla2tools._get_version", return_value="2.19")


def test_download_create(mock_config, mock_requests, mock_check_java, mock_get_version, capsys):
    """Test downloading when file does not exist."""
    _, cache_dir = mock_config
    jar_path = cache_dir / "tla2tools.jar"

    # Mock successful response with content
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_response.headers = {}
    mock_requests.return_value = mock_response

    download_tla2tools.tla(nightly=False)

    assert jar_path.exists()
    assert jar_path.read_bytes() == b"chunk1chunk2"
    mock_requests.assert_called_once()
    assert mock_requests.call_args[0][0] == "http://stable.url"

    captured = capsys.readouterr()
    assert "Created" in captured.out


def test_download_update(mock_config, mock_requests, mock_check_java, mock_get_version, capsys):
    """Test updating when file exists and is modified."""
    _, cache_dir = mock_config
    jar_path = cache_dir / "tla2tools.jar"
    jar_path.write_text("old content")

    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"new content"]
    mock_response.headers = {}
    mock_requests.return_value = mock_response

    download_tla2tools.tla(nightly=True)

    assert jar_path.read_text() == "new content"
    mock_requests.assert_called_once()
    assert mock_requests.call_args[0][0] == "http://nightly.url"
    # Check headers
    headers = mock_requests.call_args[1]["headers"]
    assert "If-Modified-Since" in headers

    captured = capsys.readouterr()
    assert "Updated" in captured.out


def test_download_no_update(mock_config, mock_requests, mock_check_java, mock_get_version, capsys):
    """Test no update when server returns 304."""
    _, cache_dir = mock_config
    jar_path = cache_dir / "tla2tools.jar"
    jar_path.write_text("content")

    # Mock 304 response
    mock_response = MagicMock()
    mock_response.status_code = 304
    mock_requests.return_value = mock_response

    download_tla2tools.tla(nightly=False)

    assert jar_path.read_text() == "content"

    captured = capsys.readouterr()
    assert "already at the latest version" in captured.out


def test_download_failure(mock_config, mock_requests, mock_check_java):
    """Test download failure raises Exit."""
    mock_requests.side_effect = requests.RequestException("Network error")

    with pytest.raises(typer.Exit) as e:
        download_tla2tools.tla(nightly=False)
    assert e.value.exit_code == 1


def test_java_check_failure(mock_config, mock_requests, mock_check_java, capsys):
    """Test that failed java check aborts download and prints error."""
    # Mock check_java_version to raise Exit (simulating failure)
    # Note: check_java_version prints error messages itself before raising,
    # but since we are mocking it, we can simulate the side effect of printing too if needed,
    # or just trust that it raises.
    # The requirement is "check the message if the java version is not adequate".
    # Since specific error message comes from check_java_version implementation (which is mocked here),
    # we simulate what check_java_version does: print error then raise.

    def side_effect(min_version):
        typer.echo(f"Error: Java version {min_version} or higher is required.", err=True)
        raise typer.Exit(1)

    mock_check_java.side_effect = side_effect

    with pytest.raises(typer.Exit) as e:
        download_tla2tools.tla(nightly=False)
    assert e.value.exit_code == 1

    # Verify download was NOT called
    mock_requests.assert_not_called()

    # Verify error message
    captured = capsys.readouterr()
    assert "Error: Java version 11 or higher is required." in captured.err
