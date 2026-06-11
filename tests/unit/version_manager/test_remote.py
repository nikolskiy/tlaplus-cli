import json

from tlaplus_cli.versioning import FetchStatus, fetch_remote_versions


def test_fetch_remote_versions_parses_fixtures(fixtures_dir, mocker, mock_cache):
    """Test fetch_remote_versions using fixture data and mocking HTTP."""
    with (fixtures_dir / "tags.json").open() as f:
        tags_data = json.load(f)
    with (fixtures_dir / "releases.json").open() as f:
        releases_data = json.load(f)

    def mock_get(url, *args, **kwargs):
        mock_resp = mocker.MagicMock()
        if "tags" in url:
            mock_resp.json.return_value = tags_data
        else:
            mock_resp.json.return_value = releases_data
        mock_resp.raise_for_status = mocker.MagicMock()
        return mock_resp

    mocker.patch("requests.get", side_effect=mock_get)

    # We need to clear cache to ensure it goes ONLINE
    cache_file = mock_cache / "github_cache.json"
    if cache_file.exists():
        cache_file.unlink()

    versions, status = fetch_remote_versions(
        "https://api.github.com/repos/tlaplus/tlaplus/tags", "https://api.github.com/repos/tlaplus/tlaplus/releases"
    )

    assert status == FetchStatus.ONLINE

    # Check v1.8.0
    v1_8 = next((v for v in versions if v.name == "v1.8.0"), None)
    assert v1_8 is not None
    assert v1_8.prerelease is True
    assert v1_8.published_at == "2026-03-27T00:12:51Z"

    # Check v1.7.4
    v1_7_4 = next((v for v in versions if v.name == "v1.7.4"), None)
    assert v1_7_4 is not None
    assert v1_7_4.prerelease is False
    assert v1_7_4.published_at == "2024-08-05T20:16:41Z"
