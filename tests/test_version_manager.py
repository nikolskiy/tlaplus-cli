import json
from pathlib import Path

from tlaplus_cli.version_manager import RemoteVersion, _process_remote_versions, write_version_metadata


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
