import shutil

import typer

from tlaplus_cli.cmd.tools import app
from tlaplus_cli.config.loader import cache_dir
from tlaplus_cli.versioning import (
    clear_pin,
    get_pinned_version_dir,
    list_local_versions,
    resolve_latest_version,
    set_pin,
)
from tlaplus_cli.versioning.schema import LocalVersion


def _resolve_uninstall_targets(version: str, all_tags: bool) -> list[LocalVersion]:
    local_versions = list_local_versions()
    matching = [lv for lv in local_versions if lv.name == version]

    if not matching:
        typer.echo(f"Error: Version {version} not found locally.", err=True)
        raise typer.Exit(1)

    matching.sort(key=lambda x: x.path.name)

    if len(matching) > 1 and not all_tags:
        typer.echo("Multiple versions match:")
        for i, lv in enumerate(matching):
            typer.echo(f"[{i}] {lv.path.name}")
        choice = typer.prompt("Select version to uninstall", type=int)
        if 0 <= choice < len(matching):
            return [matching[choice]]
        typer.echo("Invalid choice.", err=True)
        raise typer.Exit(1)

    return matching


@app.command()
def uninstall(
    version: str = typer.Argument(None),
    all: bool = typer.Option(False, "--all", help="Remove all matching versions."),
) -> None:
    if not version:
        typer.echo("Error: Please provide a version to uninstall, or 'default' to remove legacy jar.", err=True)
        raise typer.Exit(1)

    if version == "default":
        legacy = cache_dir() / "tla2tools.jar"
        if legacy.exists():
            legacy.unlink()
            typer.echo("Legacy tla2tools.jar removed.")
        else:
            typer.echo("No legacy tla2tools.jar found.")
        return

    targets = _resolve_uninstall_targets(version, all)

    pinned_dir = get_pinned_version_dir()
    pinned_dir_name = pinned_dir.name if pinned_dir else None
    uninstalled_pinned = False

    for lv in targets:
        if pinned_dir_name and pinned_dir_name == lv.path.name:
            confirm = typer.confirm(
                f"Version {lv.path.name} is currently pinned. Uninstalling it will break `tla tlc`. Continue?"
            )
            if not confirm:
                typer.echo("Aborted.")
                continue
            clear_pin()
            uninstalled_pinned = True
            typer.echo(f"Unpinned {lv.path.name}.")

        shutil.rmtree(lv.path)
        typer.echo(f"Uninstalled {lv.path.name}.")

    if uninstalled_pinned:
        remaining = list_local_versions()
        latest = resolve_latest_version(remaining)
        if latest:
            set_pin(latest.path)
            typer.echo(f"Pin fell back to {latest.path.name}")
        else:
            typer.echo("No versions remaining, pin removed.")
