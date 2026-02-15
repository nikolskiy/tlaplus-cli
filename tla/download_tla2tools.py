"""Download tla2tools.jar into the cache directory."""

import os
import subprocess
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests
import typer

from tla.check_java import check_java_version
from tla.config import cache_dir, load_config


def _get_version(jar_path: Path) -> str | None:
    """Run TLC to extract the version string, or None if java is unavailable."""
    try:
        result = subprocess.run(
            ["java", "-cp", str(jar_path), "tlc2.TLC"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout + result.stderr
        for line in output.splitlines():
            if "Version" in line:
                parts = line.split()
                idx = parts.index("Version")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        typer.echo("Warning: Timed out trying to get TLC version.", err=True)
    return None


def _set_file_mtime(path: Path, last_modified: str) -> None:
    """Set file modification time from an HTTP Last-Modified header value."""
    try:
        dt = parsedate_to_datetime(last_modified)
        mtime = dt.timestamp()
        os.utime(path, (mtime, mtime))
    except Exception as e:
        typer.echo(f"Warning: could not set mtime: {e}", err=True)


def download(jar_path: Path, url: str) -> str:
    """Download the jar. Returns 'created', 'updated', or 'no_update'."""
    headers: dict[str, str] = {}

    if jar_path.exists():
        mtime = jar_path.stat().st_mtime
        dt = datetime.fromtimestamp(mtime, tz=UTC)
        headers["If-Modified-Since"] = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

    typer.echo(f"Downloading {jar_path.name}...")
    resp = requests.get(url, headers=headers, stream=True, timeout=120, allow_redirects=True)

    if resp.status_code == 304:
        return "no_update"

    resp.raise_for_status()

    jar_path.parent.mkdir(parents=True, exist_ok=True)
    existed = jar_path.exists()

    total_size = int(resp.headers.get("content-length", 0))

    with jar_path.open("wb") as f, typer.progressbar(length=total_size, label="Downloading") as progress:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            progress.update(len(chunk))

    if "Last-Modified" in resp.headers:
        _set_file_mtime(jar_path, resp.headers["Last-Modified"])

    return "updated" if existed else "created"


def tla(
    nightly: bool = typer.Option(False, "--nightly", help="Download nightly build instead of stable."),
) -> None:
    """Download or update tla2tools.jar."""

    config = load_config()

    # Check Java version before proceeding
    check_java_version(config.java.min_version)

    url = config.tla.urls.nightly if nightly else config.tla.urls.stable
    jar_path = cache_dir() / config.tla.jar_name

    try:
        result = download(jar_path, url)
    except requests.RequestException as e:
        typer.echo(f"Error: could not download {config.tla.jar_name}: {e}", err=True)
        raise typer.Exit(1) from None

    version = _get_version(jar_path)
    version_str = f" (version {version})" if version else ""

    if result == "created":
        typer.echo(f"Created {jar_path}{version_str}")
    elif result == "updated":
        typer.echo(f"Updated {jar_path}{version_str}")
    else:
        typer.echo(f"{config.tla.jar_name} is already at the latest version{version_str}")
