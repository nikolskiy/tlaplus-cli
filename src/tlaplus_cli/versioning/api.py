import time
from pathlib import Path
from typing import Any

import requests
import typer

from tlaplus_cli.cache.github import load_github_cache, save_github_cache
from tlaplus_cli.versioning.paths import get_github_cache_file
from tlaplus_cli.versioning.schema import FetchStatus, RemoteVersion


def _load_from_cache(cache_file: Path) -> list[RemoteVersion] | None:
    return load_github_cache(cache_file)


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
    except Exception as e:
        typer.echo(f"⚠ Warning: Failed to fetch remote versions: {e}", err=True)
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
    save_github_cache(cache_file, versions)

    return versions, FetchStatus.ONLINE


def cast_str(value: Any) -> str:
    return str(value) if value is not None else ""
