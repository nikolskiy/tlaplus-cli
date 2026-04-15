from tlaplus_cli.version_manager import list_local_versions


def test_list_local_versions_timestamp_tag(mock_cache):
    """URL-installed versions whose suffix is a timestamp are parsed correctly."""

    tools_dir = mock_cache / "tools"
    tools_dir.mkdir()

    ts_dir = tools_dir / "v1.9.0-2026-04-06T12:51:28Z"
    ts_dir.mkdir()
    (ts_dir / "tla2tools.jar").write_bytes(b"jar")

    versions = list_local_versions()
    assert len(versions) == 1
    lv = versions[0]
    assert lv.name == "v1.9.0"
    assert lv.short_sha == "2026-04-06T12:51:28Z"


def test_list_local_versions_sha_tag(mock_cache):
    """Standard SHA-tagged versions still parse correctly after the split change."""

    tools_dir = mock_cache / "tools"
    tools_dir.mkdir()

    sha_dir = tools_dir / "v1.8.0-aaaaaaa"
    sha_dir.mkdir()
    (sha_dir / "tla2tools.jar").write_bytes(b"jar")

    versions = list_local_versions()
    assert len(versions) == 1
    assert versions[0].name == "v1.8.0"
    assert versions[0].short_sha == "aaaaaaa"
