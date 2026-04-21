import shutil
from pathlib import Path

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
    if version:
        local_versions = list_local_versions()
        matching = [lv for lv in local_versions if lv.name == version]
        if not matching:
            typer.echo(f"Version {version} not found locally. Installing instead.")
            return version, None
        return version, matching[0].path

    if not pinned_dir:
        typer.echo("Error: No pinned version to upgrade and no version specified.", err=True)
        raise typer.Exit(1)

    parts = pinned_dir.name.rsplit("-", 1)
    target_name = parts[0] if len(parts) == 2 else pinned_dir.name
    return target_name, pinned_dir


@app.command()
def upgrade(version: str = typer.Argument(None)) -> None:
    pinned_dir = get_pinned_version_dir()
    pinned_dir_name = pinned_dir.name if pinned_dir else None

    target_name, old_dir = _resolve_upgrade_target(version, pinned_dir)

    config = load_config()
    versions, _ = fetch_remote_versions(config.tla.urls.tags, config.tla.urls.releases, config.tla.urls.per_page)
    if not versions:
        typer.echo("Error: Unable to fetch remote versions.", err=True)
        raise typer.Exit(1)

    remote_target = next((v for v in versions if v.name == target_name), None)
    if not remote_target:
        typer.echo(f"Error: Version {target_name} not found in remote repository.", err=True)
        raise typer.Exit(1)

    if old_dir and old_dir.name == f"{remote_target.name}-{remote_target.short_sha}":
        typer.echo(f"Version {target_name} is already up to date ({remote_target.short_sha}).")
        return

    if old_dir:
        typer.echo(f"Upgrading {target_name} to {remote_target.short_sha}...")
    else:
        typer.echo(f"Installing {target_name} ({remote_target.short_sha})...")

    was_pinned = old_dir and pinned_dir_name == old_dir.name

    try:
        new_dir = download_version(remote_target)
        typer.echo("Download complete.")
    except Exception as e:
        typer.echo(f"Error: Failed to download: {e}", err=True)
        raise typer.Exit(1) from e

    if old_dir and old_dir.exists() and old_dir != new_dir:
        shutil.rmtree(old_dir, ignore_errors=True)
        typer.echo(f"Removed old version directory {old_dir.name}")

    if was_pinned or not pinned_dir:
        set_pin(new_dir)
        typer.echo(f"Updated pin to {new_dir.name}")
