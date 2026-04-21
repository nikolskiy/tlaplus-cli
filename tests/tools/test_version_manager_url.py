import pytest

from tlaplus_cli.versioning import download_version_from_url


@pytest.fixture
def mock_url_download(mocker):
    url = "https://example.com/v1.9.0/tla2tools.jar"
    fake_ts = "2026-04-06T12:51:28Z"

    mocker.patch("tlaplus_cli.versioning.downloader._utc_now_iso", return_value=fake_ts)
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.headers = {"content-length": "16"}
    mock_response.iter_content.return_value = [b"fake jar content"]
    mocker.patch("tlaplus_cli.versioning.downloader.requests.get", return_value=mock_response)
    mocker.patch("tlaplus_cli.versioning.downloader.write_version_metadata_from_url")
    return url, fake_ts


def test_download_version_from_url_creates_dir(mock_url_download, mock_cache):
    """A valid URL creates the expected version directory."""
    url, fake_ts = mock_url_download
    result_dir = download_version_from_url(url)
    tools_dir = mock_cache / "tools"
    assert result_dir == tools_dir / f"v1.9.0-{fake_ts}"
    assert result_dir.exists()


def test_download_version_from_url_writes_jar(mock_url_download, mock_cache):
    """The jar file is written into the version directory."""
    url, _ = mock_url_download
    result_dir = download_version_from_url(url)
    jar = result_dir / "tla2tools.jar"
    assert jar.exists()
    assert jar.read_bytes() == b"fake jar content"


def test_download_version_from_url_no_version_raises(mocker, mock_cache):
    """A URL with no semver segment raises ValueError."""
    url = "https://example.com/latest/tla2tools.jar"
    with pytest.raises(ValueError, match="version"):
        download_version_from_url(url)


def test_download_version_from_url_cleans_up_on_failure(mocker, mock_cache):
    """The version directory is removed if the download fails."""
    url = "https://example.com/v1.9.0/tla2tools.jar"
    fake_ts = "2026-04-06T12:51:28Z"
    mocker.patch("tlaplus_cli.versioning.downloader._utc_now_iso", return_value=fake_ts)
    mocker.patch(
        "tlaplus_cli.versioning.downloader.requests.get",
        side_effect=Exception("network error"),
    )

    with pytest.raises(Exception, match="network error"):
        download_version_from_url(url)

    tools_dir = mock_cache / "tools"
    version_dir = tools_dir / f"v1.9.0-{fake_ts}"
    assert not version_dir.exists()
