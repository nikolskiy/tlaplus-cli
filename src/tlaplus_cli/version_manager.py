from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import requests
import typer
from rich.progress import BarColumn, DownloadColumn, Progress, TransferSpeedColumn

from tlaplus_cli.config import cache_dir

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def is_url(text: str) -> bool:
    """Return True if *text* looks like an HTTP(S) URL."""
    return text.lower().startswith(("http://", "https://"))


def extract_version_from_url(url: str) -> str | None:
    """Scan URL path segments for a semver-like segment (e.g. 'v1.8.0').

    Returns the first matching segment, or None if none is found.
    """
    path = urlparse(url).path
    for segment in path.split("/"):
        if _SEMVER_RE.match(segment):
            return segment
    return None


def _utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 format, e.g. '2026-04-06T12:51:28Z'."""
    now = datetime.now(tz=UTC)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def download_version_from_url(url: str) -> Path:
    """Download tla2tools.jar from *url* and store it in a timestamped version directory.

    The version name is extracted from URL path segments.  The tag (directory suffix) is
    the ISO 8601 download timestamp.

    Raises:
        ValueError: if no semver segment can be found in the URL.
    """
    version_name = extract_version_from_url(url)
    if version_name is None:
        msg = (
            'could not extract a version name from the URL. '
            'The URL must contain a version segment (e.g. "v1.8.0").'
        )
        raise ValueError(msg)

    tag = _utc_now_iso()
    tools_dir = get_tools_dir()
    version_dir = tools_dir / f"{version_name}-{tag}"
    version_dir.mkdir(parents=True, exist_ok=True)
    jar_path = version_dir / "tla2tools.jar"

    try:
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
            task = progress.add_task(f"Downloading {version_name}...", total=total or None)
            with jar_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
    except Exception:
        shutil.rmtree(version_dir, ignore_errors=True)
        raise

    write_version_metadata_from_url(version_dir, version_name=version_name, tag=tag, url=url)
    return version_dir


def write_version_metadata_from_url(
    version_dir: Path,
    *,
    version_name: str,
    tag: str,
    url: str,
) -> None:
    """Write meta-tla2tools.json for a URL-sourced install."""
    tlc2_version_string = ""
    try:
        result = subprocess.run(
            ["java", "-cp", "tla2tools.jar", "tlc2.TLC", "-version"],
            cwd=version_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            tlc2_version_string = result.stdout.strip().split("\n")[0]
    except Exception as e:
        typer.echo(f"Warning: Failed to extract TLC version string: {e}", err=True)

    meta_file = version_dir / "meta-tla2tools.json"
    metadata = {
        "tag_name": version_name,
        "sha": "",
        "published_at": "",
        "tlc2_version_string": tlc2_version_string,
        "prerelease": False,
        "download_url": url,
        "tag": tag,
    }

    try:
        with meta_file.open("w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        typer.echo(f"Warning: Failed to write metadata: {e}", err=True)


def _parse_semver(name: str) -> tuple[int, int, int] | None:
    """Try to extract (major, minor, patch) from a version name like 'v1.8.0'."""
    m = _SEMVER_RE.match(name)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None


def _version_sort_key(lv: LocalVersion) -> tuple[int, tuple[int, int, int], str, float]:
    """
    Build a sort key for determining the "latest" installed version.

    Tuple structure (all compared descending):
      0: has_semver  — 1 if parseable, 0 otherwise (semver > non-semver)
      1: semver      — (major, minor, patch) tuple
      2: published_at — ISO-8601 string from metadata (lexicographic comparison works)
      3: mtime       — directory last-modified timestamp
    """
    semver = _parse_semver(lv.name)
    has_semver = 1 if semver else 0
    semver_tuple = semver if semver else (0, 0, 0)

    published_at = ""
    meta = read_version_metadata(lv.path)
    if meta and meta.get("published_at"):
        published_at = meta["published_at"]

    try:
        mtime = lv.path.stat().st_mtime
    except OSError:
        mtime = 0.0

    return (has_semver, semver_tuple, published_at, mtime)


def resolve_latest_version(versions: Sequence[LocalVersion]) -> LocalVersion | None:
    """Return the 'latest' version from a list, or None if empty.

    Ordering priority:
      1. Highest semantic version wins.
      2. For equal/unparseable semver: latest published_at from meta-tla2tools.json.
      3. For missing metadata: latest directory mtime.
    """
    if not versions:
        return None
    return max(versions, key=_version_sort_key)


@dataclass
class RemoteVersion:
    name: str
    short_sha: str
    full_sha: str
    jar_download_url: str
    published_at: str
    prerelease: bool


@dataclass
class LocalVersion:
    name: str
    short_sha: str
    path: Path


class FetchStatus(Enum):
    ONLINE = "online"
    CACHED = "cached"
    STALE = "stale"
    UNAVAILABLE = "unavailable"


def get_github_cache_file() -> Path:
    return cache_dir() / "github_cache.json"


def get_tools_dir() -> Path:
    return cache_dir() / "tools"


def get_pinned_path() -> Path:
    """Returns path to the pin marker file."""
    return get_tools_dir() / "tools-pinned-version.txt"


def get_pinned_version_dir() -> Path | None:
    """Returns the pinned version directory, or None if not pinned."""
    _migrate_legacy_pin()
    pin_file = get_pinned_path()
    if not pin_file.exists():
        return None
    dir_name = pin_file.read_text().strip()
    if not dir_name:
        return None
    target = get_tools_dir() / dir_name
    return target if target.is_dir() else None


def _migrate_legacy_pin() -> None:
    """Migrate legacy cache directory and pin files."""
    old_dir = cache_dir() / "tlc"
    new_dir = get_tools_dir()

    # 1. Migrate directory
    if old_dir.exists() and not new_dir.exists():
        try:
            old_dir.rename(new_dir)
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to migrate legacy cache: {e}", err=True)

    # 2. Migrate legacy symlink pin
    legacy_symlink = new_dir / "pinned"
    if legacy_symlink.is_symlink():
        try:
            target_name = legacy_symlink.readlink().name
            legacy_symlink.unlink()
            get_pinned_path().write_text(target_name)
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to migrate legacy symlink pin: {e}", err=True)

    # 3. Migrate legacy filename tlc-pinned-version.txt -> tools-pinned-version.txt
    old_pin_file = new_dir / "tlc-pinned-version.txt"
    new_pin_file = get_pinned_path()
    if old_pin_file.exists() and not new_pin_file.exists():
        try:
            old_pin_file.rename(new_pin_file)
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to migrate legacy pin file: {e}", err=True)


def set_pin(version_dir: Path) -> None:
    """Pin a version by writing its directory name to tools-pinned-version.txt."""
    pin_file = get_pinned_path()
    pin_file.parent.mkdir(parents=True, exist_ok=True)
    pin_file.write_text(version_dir.name)


def clear_pin() -> None:
    """Remove the pin."""
    pin_file = get_pinned_path()
    if pin_file.exists():
        pin_file.unlink()


def list_local_versions() -> list[LocalVersion]:
    tools_dir = get_tools_dir()
    if not tools_dir.exists():
        return []
    result = []
    for d in tools_dir.iterdir():
        if d.is_dir() and not d.is_symlink():
            # Split on the FIRST hyphen so timestamp suffixes are preserved whole
            parts = d.name.split("-", 1)
            if len(parts) == 2:
                result.append(LocalVersion(name=parts[0], short_sha=parts[1], path=d))
    return result


def write_version_metadata(version_dir: Path, target: RemoteVersion) -> None:
    """Write the meta-tla2tools.json file for a downloaded version."""
    tlc2_version_string = ""
    try:
        result = subprocess.run(
            ["java", "-cp", "tla2tools.jar", "tlc2.TLC", "-version"],
            cwd=version_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            tlc2_version_string = result.stdout.strip().split("\n")[0]
    except Exception as e:
        typer.echo(f"⚠ Warning: Failed to extract TLC version string: {e}", err=True)

    meta_file = version_dir / "meta-tla2tools.json"
    metadata = {
        "tag_name": target.name,
        "sha": target.full_sha,
        "published_at": target.published_at,
        "tlc2_version_string": tlc2_version_string,
        "prerelease": target.prerelease,
        "download_url": target.jar_download_url,
    }

    try:
        with meta_file.open("w") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        typer.echo(f"⚠ Warning: Failed to write metadata: {e}", err=True)


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
    except Exception:
        return None


def clear_cache() -> None:
    cache_file = get_github_cache_file()
    if cache_file.exists():
        cache_file.unlink()


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
        response = requests.get(
            target.jar_download_url,
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
            task = progress.add_task(f"Downloading {target.name}...", total=total or None)
            with jar_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
    except Exception:
        shutil.rmtree(version_dir, ignore_errors=True)
        raise

    write_version_metadata(version_dir, target)

    return version_dir


def _load_from_cache(cache_file: Path) -> list[RemoteVersion] | None:
    if cache_file.exists():
        try:
            with cache_file.open("r") as f:
                data = json.load(f)
            return [RemoteVersion(**item) for item in data]
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to read cache: {e}", err=True)
    return None


def _fetch_from_api(
    tags_url: str, releases_url: str, per_page: int = 30
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    try:
        params = {"per_page": per_page}
        tags_response = requests.get(tags_url, params=params, timeout=10)
        tags_response.raise_for_status()
        tags_data: list[dict[str, Any]] = tags_response.json()

        releases_response = requests.get(releases_url, params=params, timeout=10)
        releases_response.raise_for_status()
        releases_data: list[dict[str, Any]] = releases_response.json()
    except requests.RequestException:
        return None
    else:
        return tags_data, releases_data


def _process_remote_versions(
    tags_data: list[dict[str, Any]], releases_data: list[dict[str, Any]]
) -> list[RemoteVersion]:
    releases_by_tag = {cast_str(r.get("tag_name")): r for r in releases_data if "tag_name" in r}
    versions = []

    for tag in tags_data:
        name = cast_str(tag.get("name"))
        if not name or name not in releases_by_tag:
            continue

        release = releases_by_tag[name]
        assets = release.get("assets", [])
        jar_url = None
        for asset in assets:
            if asset.get("name") == "tla2tools.jar":
                jar_url = cast_str(asset.get("browser_download_url"))
                break

        if jar_url:
            commit = tag.get("commit", {})
            full_sha = cast_str(commit.get("sha", ""))
            if full_sha:
                versions.append(
                    RemoteVersion(
                        name=name,
                        short_sha=full_sha[:7],
                        full_sha=full_sha,
                        jar_download_url=jar_url,
                        published_at=cast_str(release.get("published_at")),
                        prerelease=bool(release.get("prerelease")),
                    )
                )
    return versions


def fetch_remote_versions(
    tags_url: str, releases_url: str, per_page: int = 30
) -> tuple[list[RemoteVersion], FetchStatus]:
    cache_file = get_github_cache_file()

    # Check cache TTL
    if cache_file.exists():
        try:
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime < 3600:
                cached_data = _load_from_cache(cache_file)
                if cached_data is not None:
                    return cached_data, FetchStatus.CACHED
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to check cache age: {e}", err=True)

    # Fetch from API
    api_data = _fetch_from_api(tags_url, releases_url, per_page)
    if not api_data:
        # Fallback to stale cache if available
        cached_data = _load_from_cache(cache_file)
        if cached_data is not None:
            return cached_data, FetchStatus.STALE
        return [], FetchStatus.UNAVAILABLE

    tags_data, releases_data = api_data
    versions = _process_remote_versions(tags_data, releases_data)

    # Save to cache
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with cache_file.open("w") as f:
            json.dump([asdict(v) for v in versions], f)
    except Exception as e:
        typer.echo(f"⚠ Warning: Failed to save cache: {e}", err=True)

    return versions, FetchStatus.ONLINE


def cast_str(value: Any) -> str:
    return str(value) if value is not None else ""
