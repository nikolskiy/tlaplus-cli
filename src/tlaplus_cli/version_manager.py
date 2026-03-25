import json
import shutil
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import requests
import typer
from rich.progress import BarColumn, DownloadColumn, Progress, TransferSpeedColumn

from tlaplus_cli.config import cache_dir


@dataclass
class RemoteVersion:
    name: str
    short_sha: str
    full_sha: str
    jar_download_url: str


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


def get_tlc_dir() -> Path:
    return cache_dir() / "tlc"


def get_pinned_path() -> Path:
    """Returns path to the pin marker file."""
    return get_tlc_dir() / "tlc-pinned-version.txt"


def get_pinned_version_dir() -> Path | None:
    """Returns the pinned version directory, or None if not pinned."""
    _migrate_legacy_pin()
    pin_file = get_pinned_path()
    if not pin_file.exists():
        return None
    dir_name = pin_file.read_text().strip()
    if not dir_name:
        return None
    target = get_tlc_dir() / dir_name
    return target if target.is_dir() else None


def _migrate_legacy_pin() -> None:
    """Migrate old symlink-based pin to text file."""
    legacy_pin = get_tlc_dir() / "pinned"
    if legacy_pin.is_symlink():
        try:
            target_name = legacy_pin.readlink().name
            legacy_pin.unlink()
            pin_file = get_pinned_path()
            pin_file.write_text(target_name)
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to migrate legacy pin: {e}", err=True)


def set_pin(version_dir: Path) -> None:
    """Pin a version by writing its directory name to tlc-pinned-version.txt."""
    pin_file = get_pinned_path()
    pin_file.parent.mkdir(parents=True, exist_ok=True)
    pin_file.write_text(version_dir.name)


def clear_pin() -> None:
    """Remove the pin."""
    pin_file = get_pinned_path()
    if pin_file.exists():
        pin_file.unlink()


def list_local_versions() -> list[LocalVersion]:
    tlc_dir = get_tlc_dir()
    if not tlc_dir.exists():
        return []
    result = []
    for d in tlc_dir.iterdir():
        if d.is_dir() and not d.is_symlink():
            parts = d.name.rsplit("-", 1)
            if len(parts) == 2:
                result.append(LocalVersion(name=parts[0], short_sha=parts[1], path=d))
    return result


def clear_cache() -> None:
    cache_file = get_github_cache_file()
    if cache_file.exists():
        cache_file.unlink()


def download_version(target: RemoteVersion, *, force: bool = False) -> Path:
    """Download a TLC version jar. Returns the version directory path."""
    tlc_dir = get_tlc_dir()
    version_dir = tlc_dir / f"{target.name}-{target.short_sha}"

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
