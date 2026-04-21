import json
import subprocess

from tlaplus_cli.versioning import (
    RemoteVersion,
    write_version_metadata,
    write_version_metadata_from_url,
)


def test_write_version_metadata(tmp_path, mocker):

    version_dir = tmp_path / "v1.8.0-aaaaaaa"
    version_dir.mkdir()

    mock_run = mocker.patch("tlaplus_cli.versioning.metadata.subprocess.run")
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


def test_write_version_metadata_from_url_creates_file(tmp_path, mocker):

    mock_run = mocker.patch("tlaplus_cli.versioning.metadata.subprocess.run")
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
        "tlaplus_cli.versioning.metadata.subprocess.run",
        side_effect=subprocess.SubprocessError("java not found"),
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
