import pytest

from tlaplus_cli.version_manager import RemoteVersion, download_version


def test_download_version_cleanup_on_failure(mocker, mock_cache):
    """If download fails, the partial version directory should be removed."""
    target = RemoteVersion(
        name="v1.8.0",
        short_sha="aaaaaaa",
        full_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        jar_download_url="http://example.com/fail",
        published_at="2024-01-01T00:00:00Z",
        prerelease=False,
    )

    # Mock requests.get to raise an exception
    mocker.patch("requests.get", side_effect=Exception("Network error"))

    version_dir = mock_cache / "tools" / "v1.8.0-aaaaaaa"

    with pytest.raises(Exception, match="Network error"):
        download_version(target)

    assert not version_dir.exists()


def test_download_version_force_removes_existing(mocker, mock_cache):
    """If force=True, existing directory is removed and recreated."""
    target = RemoteVersion(
        name="v1.8.0",
        short_sha="aaaaaaa",
        full_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        jar_download_url="http://example.com/jar",
        published_at="2024-01-01T00:00:00Z",
        prerelease=False,
    )

    version_dir = mock_cache / "tools" / "v1.8.0-aaaaaaa"
    version_dir.mkdir(parents=True)
    old_file = version_dir / "old.txt"
    old_file.write_text("old")

    # Mock requests.get to succeed but do nothing
    mock_response = mocker.MagicMock()
    mock_response.iter_content.return_value = [b"new content"]
    mock_response.headers = {}
    mocker.patch("requests.get", return_value=mock_response)
    mocker.patch("tlaplus_cli.version_manager.write_version_metadata")

    download_version(target, force=True)

    assert version_dir.exists()
    assert not old_file.exists()
    assert (version_dir / "tla2tools.jar").exists()
