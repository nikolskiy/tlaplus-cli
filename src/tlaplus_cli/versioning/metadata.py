import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tlaplus_cli.ui import warn
from tlaplus_cli.versioning.schema import RemoteVersion


def _utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 format, e.g. '2026-04-06T12:51:28Z'."""
    now = datetime.now(tz=UTC)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_tlc_version(version_dir: Path) -> str:
    """Run java to get the TLC version string."""
    try:
        result = subprocess.run(
            ["java", "-cp", "tla2tools.jar", "tlc2.TLC", "-version"],
            cwd=version_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            return result.stdout.strip().split("\n")[0]
    except (subprocess.SubprocessError, OSError) as e:
        warn(f"Failed to extract TLC version string: {e}")
    return ""


def _write_metadata(version_dir: Path, metadata: dict[str, Any]) -> None:
    """Write metadata dict to meta-tla2tools.json."""
    meta_file = version_dir / "meta-tla2tools.json"
    try:
        with meta_file.open("w") as f:
            json.dump(metadata, f, indent=2)
    except OSError as e:
        warn(f"Failed to write metadata: {e}")


def write_version_metadata(version_dir: Path, target: RemoteVersion) -> None:
    """Write the meta-tla2tools.json file for a downloaded version."""
    tlc2_version_string = _extract_tlc_version(version_dir)
    metadata = {
        "tag_name": target.name,
        "sha": target.full_sha,
        "published_at": target.published_at,
        "tlc2_version_string": tlc2_version_string,
        "prerelease": target.prerelease,
        "download_url": target.jar_download_url,
    }
    _write_metadata(version_dir, metadata)


def read_version_metadata(version_dir: Path) -> dict[str, Any] | None:
    """Read the meta-tla2tools.json file for a version directory.

    Returns the metadata dict or None if the file doesn't exist or can't be read.
    """
    meta_file = version_dir / "meta-tla2tools.json"
    if not meta_file.exists():
        return None
    try:
        with meta_file.open("r") as f:
            data: dict[str, Any] = json.load(f)
            return data
    except (json.JSONDecodeError, OSError):
        return None


def write_version_metadata_from_url(
    version_dir: Path,
    *,
    version_name: str,
    tag: str,
    url: str,
) -> None:
    """Write meta-tla2tools.json for a URL-sourced install."""
    tlc2_version_string = _extract_tlc_version(version_dir)
    metadata = {
        "tag_name": version_name,
        "sha": "",
        "published_at": "",
        "tlc2_version_string": tlc2_version_string,
        "prerelease": False,
        "download_url": url,
        "tag": tag,
    }
    _write_metadata(version_dir, metadata)
