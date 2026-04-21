import shutil
from pathlib import Path

import requests
import typer

from tlaplus_cli.cmd.tools import app
from tlaplus_cli.config.loader import load_config
from tlaplus_cli.versioning import (
    download_version,
    fetch_remote_versions,
    get_pinned_version_dir,
    list_local_versions,
    set_pin,
)


def _resolve_upgrade_target(version: str | None, pinned_dir: Path | None) -> tuple[str, Path | None]:
    """Determine which version to upgrade and its local path."""
    if version:
        local_versions = list_local_versions()
        matching = [lv for lv in local_versions if lv.name == version]
        return version, (matching[0].path if matching else None)

    if not pinned_dir:
        typer.echo("Error: No version specified and no version is pinned.", err=True)
        raise typer.Exit(1)

    # Extract version name from directory (e.g., 'v1.8.0-abcdef1' -> 'v1.8.0')
    parts = pinned_dir.name.rsplit("-", 1)
    target_name = parts[0] if len(parts) == 2 else pinned_dir.name
    return target_name, pinned_dir


@app.command()
def upgrade(
    version: str = typer.Argument(None, help="Specific version to upgrade (optional).")
) -> None:
    """Upgrade an installed version (or the pinned version) to its latest remote build."""
    pinned_dir = get_pinned_version_dir()
    target_name, local_path = _resolve_upgrade_target(version, pinned_dir)

    config = load_config()
    versions, status = fetch_remote_versions(
        config.tla.urls.tags, config.tla.urls.releases, config.tla.urls.per_page
    )

    if not versions:
        typer.echo(f"Error: Could not fetch remote versions (status: {status.value})", err=True)
        raise typer.Exit(1)

    remote = next((v for v in versions if v.name == target_name), None)
    if not remote:
        typer.echo(f"Error: Version {target_name} not found on remote.", err=True)
        raise typer.Exit(1)

    if local_path and local_path.name.endswith(f"-{remote.short_sha}"):
        typer.echo(f"Version {target_name} is already up to date ({remote.short_sha}).")
        return

    if not local_path:
        typer.echo(f"Version {target_name} not found locally. Installing instead.")
    else:
        typer.echo(f"Upgrading {target_name} to latest build ({remote.short_sha}) ...")

    try:
        new_dir = download_version(remote, force=True)
        typer.echo(f"Successfully upgraded to {new_dir}")
        # Remove old directory if it's different from the new one
        if local_path and local_path.exists() and local_path.resolve() != new_dir.resolve():
            shutil.rmtree(local_path)

    except (requests.RequestException, OSError) as e:
        typer.echo(f"Error: Failed to upgrade: {e}", err=True)
        raise typer.Exit(1) from e

    # If we upgraded the pinned version, move the pin
    if pinned_dir and local_path == pinned_dir:
        set_pin(new_dir)
        typer.echo(f"Updated pin to {new_dir.name}")
