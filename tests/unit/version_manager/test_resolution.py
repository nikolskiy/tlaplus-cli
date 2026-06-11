import json
import os
import time

from tlaplus_cli.versioning import LocalVersion, resolve_latest_version


def test_returns_none_when_no_versions():
    """No directories -> no latest version."""
    assert resolve_latest_version([]) is None


def test_single_version_returns_it(tmp_path):
    d = tmp_path / "v1.7.0-bbbbbbb"
    d.mkdir()
    versions = [LocalVersion(name="v1.7.0", short_sha="bbbbbbb", path=d)]
    result = resolve_latest_version(versions)
    assert result is not None
    assert result.name == "v1.7.0"


def test_higher_semver_wins(tmp_path):
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


def test_semver_ordering_with_many_versions(tmp_path):
    names = ["v1.5.0", "v1.8.0", "v1.7.4", "v1.6.1"]
    versions = []
    for name in names:
        d = tmp_path / f"{name}-aaaaaaa"
        d.mkdir()
        versions.append(LocalVersion(name=name, short_sha="aaaaaaa", path=d))
    result = resolve_latest_version(versions)
    assert result is not None
    assert result.name == "v1.8.0"


def test_same_semver_falls_back_to_published_at(tmp_path):
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


def test_non_semver_falls_back_to_published_at(tmp_path):
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


def test_no_metadata_falls_back_to_mtime(tmp_path):
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


def test_mixed_semver_and_non_semver(tmp_path):
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
