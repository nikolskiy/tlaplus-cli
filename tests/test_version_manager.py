import json
import os
import time
from pathlib import Path

from tlaplus_cli.version_manager import (
    LocalVersion,
    RemoteVersion,
    _process_remote_versions,
    extract_version_from_url,
    is_url,
    list_local_versions,
    resolve_latest_version,
    write_version_metadata,
    write_version_metadata_from_url,
)


class TestResolveLatestVersion:
    """Tests for the version-fallback ordering logic."""

    def test_returns_none_when_no_versions(self):
        """No directories -> no latest version."""
        assert resolve_latest_version([]) is None

    def test_single_version_returns_it(self, tmp_path):
        d = tmp_path / "v1.7.0-bbbbbbb"
        d.mkdir()
        versions = [LocalVersion(name="v1.7.0", short_sha="bbbbbbb", path=d)]
        result = resolve_latest_version(versions)
        assert result is not None
        assert result.name == "v1.7.0"

    def test_higher_semver_wins(self, tmp_path):
        d1 = tmp_path / "v1.7.0-bbbbbbb"
        d1.mkdir()
        d2 = tmp_path / "v1.8.0-aaaaaaa"
        d2.mkdir()
        versions = [
            LocalVersion(name="v1.7.0", short_sha="bbbbbbb", path=d1),
            LocalVersion(name="v1.8.0", short_sha="aaaaaaa", path=d2),
        ]
        result = resolve_latest_version(versions)
        assert result is not None
        assert result.name == "v1.8.0"

    def test_semver_ordering_with_many_versions(self, tmp_path):
        names = ["v1.5.0", "v1.8.0", "v1.7.4", "v1.6.1"]
        versions = []
        for name in names:
            d = tmp_path / f"{name}-aaaaaaa"
            d.mkdir()
            versions.append(LocalVersion(name=name, short_sha="aaaaaaa", path=d))
        result = resolve_latest_version(versions)
        assert result is not None
        assert result.name == "v1.8.0"

    def test_same_semver_falls_back_to_published_at(self, tmp_path):
        """Two tags for the same version name — the one with a later release date wins."""
        d1 = tmp_path / "v1.8.0-aaaaaaa"
        d1.mkdir()
        meta1 = {"published_at": "2024-01-01T00:00:00Z"}
        (d1 / "meta-tla2tools.json").write_text(json.dumps(meta1))

        d2 = tmp_path / "v1.8.0-bbbbbbb"
        d2.mkdir()
        meta2 = {"published_at": "2025-06-15T00:00:00Z"}
        (d2 / "meta-tla2tools.json").write_text(json.dumps(meta2))

        versions = [
            LocalVersion(name="v1.8.0", short_sha="aaaaaaa", path=d1),
            LocalVersion(name="v1.8.0", short_sha="bbbbbbb", path=d2),
        ]
        result = resolve_latest_version(versions)
        assert result is not None
        assert result.short_sha == "bbbbbbb"

    def test_non_semver_falls_back_to_published_at(self, tmp_path):
        """Non-semver names (e.g. 'nightly') use release date as primary sort."""
        d1 = tmp_path / "nightly-aaaaaaa"
        d1.mkdir()
        meta1 = {"published_at": "2025-01-01T00:00:00Z"}
        (d1 / "meta-tla2tools.json").write_text(json.dumps(meta1))

        d2 = tmp_path / "nightly-bbbbbbb"
        d2.mkdir()
        meta2 = {"published_at": "2025-06-01T00:00:00Z"}
        (d2 / "meta-tla2tools.json").write_text(json.dumps(meta2))

        versions = [
            LocalVersion(name="nightly", short_sha="aaaaaaa", path=d1),
            LocalVersion(name="nightly", short_sha="bbbbbbb", path=d2),
        ]
        result = resolve_latest_version(versions)
        assert result is not None
        assert result.short_sha == "bbbbbbb"

    def test_no_metadata_falls_back_to_mtime(self, tmp_path):
        """When meta-tla2tools.json is absent, use directory mtime."""
        d1 = tmp_path / "nightly-aaaaaaa"
        d1.mkdir()
        # Set older mtime
        old_time = time.time() - 86400
        os.utime(d1, (old_time, old_time))

        d2 = tmp_path / "nightly-bbbbbbb"
        d2.mkdir()
        # d2 has current mtime (newer)

        versions = [
            LocalVersion(name="nightly", short_sha="aaaaaaa", path=d1),
            LocalVersion(name="nightly", short_sha="bbbbbbb", path=d2),
        ]
        result = resolve_latest_version(versions)
        assert result is not None
        assert result.short_sha == "bbbbbbb"

    def test_mixed_semver_and_non_semver(self, tmp_path):
        """Semver versions should rank above non-semver."""
        d1 = tmp_path / "nightly-aaaaaaa"
        d1.mkdir()
        d2 = tmp_path / "v1.7.0-bbbbbbb"
        d2.mkdir()

        versions = [
            LocalVersion(name="nightly", short_sha="aaaaaaa", path=d1),
            LocalVersion(name="v1.7.0", short_sha="bbbbbbb", path=d2),
        ]
        result = resolve_latest_version(versions)
        assert result is not None
        assert result.name == "v1.7.0"


def test_process_remote_versions_parses_metadata():
    fixtures_dir = Path(__file__).parent / "fixtures"
    with (fixtures_dir / "tags.json").open() as f:
        tags_data = json.load(f)
    with (fixtures_dir / "releases.json").open() as f:
        releases_data = json.load(f)

    versions = _process_remote_versions(tags_data, releases_data)

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


def test_write_version_metadata(tmp_path, mocker):

    version_dir = tmp_path / "v1.8.0-aaaaaaa"
    version_dir.mkdir()

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.stdout = "TLC2 Version 2.18 of 27 March 2026 (revision 1.8.0)\n"
    mock_run.return_value.returncode = 0

    target = RemoteVersion(
        name="v1.8.0",
        short_sha="aaaaaaa",
        full_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        jar_download_url="http://example.com/tla2tools.jar",
        published_at="2026-03-27T00:12:51Z",
        prerelease=True,
    )

    write_version_metadata(version_dir, target)

    # Assert subprocess was called correctly
    mock_run.assert_called_once_with(
        ["java", "-cp", "tla2tools.jar", "tlc2.TLC", "-version"],
        cwd=version_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    # Assert json file was created
    meta_file = version_dir / "meta-tla2tools.json"
    assert meta_file.exists()

    with meta_file.open() as f:
        data = json.load(f)

    assert data["tag_name"] == "v1.8.0"
    assert data["sha"] == "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert data["published_at"] == "2026-03-27T00:12:51Z"
    assert data["tlc2_version_string"] == "TLC2 Version 2.18 of 27 March 2026 (revision 1.8.0)"
    assert data["prerelease"] is True
    assert data["download_url"] == "http://example.com/tla2tools.jar"


# --- is_url ---

def test_is_url_https():
    assert is_url("https://example.com/v1.8.0/tla2tools.jar") is True

def test_is_url_http():
    assert is_url("http://example.com/tla2tools.jar") is True

def test_is_url_version_string():
    assert is_url("v1.8.0") is False

def test_is_url_empty():
    assert is_url("") is False


# --- extract_version_from_url ---

def test_extract_version_direct_parent():
    url = "https://example.com/v1.8.0/tla2tools.jar"
    assert extract_version_from_url(url) == "v1.8.0"

def test_extract_version_nested():
    url = "https://example.com/custom/v1.8.0/build/tla2tools.jar"
    assert extract_version_from_url(url) == "v1.8.0"

def test_extract_version_no_v_prefix():
    url = "https://example.com/1.8.0/tla2tools.jar"
    assert extract_version_from_url(url) == "1.8.0"

def test_extract_version_not_found():
    url = "https://example.com/custom/latest/tla2tools.jar"
    assert extract_version_from_url(url) is None

def test_extract_version_returns_first_match():
    # Two version-like segments — must return the first one encountered
    url = "https://example.com/v1.8.0/dist/v2.0.0/tla2tools.jar"
    assert extract_version_from_url(url) == "v1.8.0"


# --- write_version_metadata_from_url ---

def test_write_version_metadata_from_url_creates_file(tmp_path, mocker):

    mock_run = mocker.patch("tlaplus_cli.version_manager.subprocess.run")
    mock_run.return_value.stdout = "TLC2 Version 2.20\nSome extra line"

    write_version_metadata_from_url(
        tmp_path,
        version_name="v1.9.0",
        tag="2026-04-06T12:51:28Z",
        url="https://example.com/v1.9.0/tla2tools.jar",
    )

    meta_file = tmp_path / "meta-tla2tools.json"
    assert meta_file.exists()

    with meta_file.open() as f:
        data = json.load(f)

    assert data["tag_name"] == "v1.9.0"
    assert data["tag"] == "2026-04-06T12:51:28Z"
    assert data["download_url"] == "https://example.com/v1.9.0/tla2tools.jar"
    assert data["sha"] == ""
    assert data["published_at"] == ""
    assert data["prerelease"] is False
    assert data["tlc2_version_string"] == "TLC2 Version 2.20"


def test_write_version_metadata_from_url_handles_subprocess_failure(tmp_path, mocker):

    mocker.patch(
        "tlaplus_cli.version_manager.subprocess.run",
        side_effect=Exception("java not found"),
    )

    write_version_metadata_from_url(
        tmp_path,
        version_name="v1.9.0",
        tag="2026-04-06T12:51:28Z",
        url="https://example.com/v1.9.0/tla2tools.jar",
    )

    meta_file = tmp_path / "meta-tla2tools.json"
    with meta_file.open() as f:
        data = json.load(f)
    assert data["tlc2_version_string"] == ""


# --- list_local_versions with timestamp tag ---

def test_list_local_versions_timestamp_tag(tmp_path, mocker):
    """URL-installed versions whose suffix is a timestamp are parsed correctly."""

    mocker.patch("tlaplus_cli.version_manager.cache_dir", return_value=tmp_path)
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()

    ts_dir = tools_dir / "v1.9.0-2026-04-06T12:51:28Z"
    ts_dir.mkdir()
    (ts_dir / "tla2tools.jar").write_bytes(b"jar")

    versions = list_local_versions()
    assert len(versions) == 1
    lv = versions[0]
    assert lv.name == "v1.9.0"
    assert lv.short_sha == "2026-04-06T12:51:28Z"


def test_list_local_versions_sha_tag(tmp_path, mocker):
    """Standard SHA-tagged versions still parse correctly after the split change."""

    mocker.patch("tlaplus_cli.version_manager.cache_dir", return_value=tmp_path)
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()

    sha_dir = tools_dir / "v1.8.0-aaaaaaa"
    sha_dir.mkdir()
    (sha_dir / "tla2tools.jar").write_bytes(b"jar")

    versions = list_local_versions()
    assert len(versions) == 1
    assert versions[0].name == "v1.8.0"
    assert versions[0].short_sha == "aaaaaaa"
