import shutil
from pathlib import Path

import requests
from rich.progress import BarColumn, DownloadColumn, Progress, TransferSpeedColumn

from tlaplus_cli.versioning.metadata import (
    _utc_now_iso,
    write_version_metadata,
    write_version_metadata_from_url,
)
from tlaplus_cli.versioning.paths import get_tools_dir
from tlaplus_cli.versioning.resolver import extract_version_from_url
from tlaplus_cli.versioning.schema import RemoteVersion


def _download_jar(url: str, jar_path: Path, label: str) -> None:
    """Download tla2tools.jar from *url* with a progress bar."""
    response = requests.get(
        url,
        stream=True,
        timeout=30,
        headers={"User-Agent": "tlaplus-cli"},
    )
    response.raise_for_status()
    total = int(response.headers.get("content-length", 0))

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
    ) as progress:
        task = progress.add_task(f"Downloading {label}...", total=total or None)
        with jar_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                progress.update(task, advance=len(chunk))


def download_version(target: RemoteVersion, *, force: bool = False) -> Path:
    """Download a TLC version jar. Returns the version directory path."""
    tools_dir = get_tools_dir()
    version_dir = tools_dir / f"{target.name}-{target.short_sha}"

    if version_dir.exists() and not force:
        return version_dir

    if version_dir.exists():
        shutil.rmtree(version_dir)

    version_dir.mkdir(parents=True, exist_ok=True)
    jar_path = version_dir / "tla2tools.jar"

    try:
        _download_jar(target.jar_download_url, jar_path, target.name)
    except (requests.RequestException, OSError):
        shutil.rmtree(version_dir, ignore_errors=True)
        raise

    write_version_metadata(version_dir, target)

    return version_dir


def download_version_from_url(url: str) -> Path:
    """Download tla2tools.jar from *url* and store it in a timestamped version directory.

    The version name is extracted from URL path segments.  The tag (directory suffix) is
    the ISO 8601 download timestamp.

    Raises:
        ValueError: if no semver segment can be found in the URL.
    """
    version_name = extract_version_from_url(url)
    if version_name is None:
        msg = 'could not extract a version name from the URL. The URL must contain a version segment (e.g. "v1.8.0").'
        raise ValueError(msg)

    tag = _utc_now_iso()
    tools_dir = get_tools_dir()
    version_dir = tools_dir / f"{version_name}-{tag}"
    version_dir.mkdir(parents=True, exist_ok=True)
    jar_path = version_dir / "tla2tools.jar"

    try:
        _download_jar(url, jar_path, version_name)
    except (requests.RequestException, OSError):
        shutil.rmtree(version_dir, ignore_errors=True)
        raise

    write_version_metadata_from_url(version_dir, version_name=version_name, tag=tag, url=url)
    return version_dir
