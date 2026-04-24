import shutil
from pathlib import Path

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


def _resolve_uninstall_targets(versions: list[str]) -> list[Path]:
    """Resolve version names to local directory paths."""
    local_versions = list_local_versions()
    targets: list[Path] = []
    for v in versions:
        if v == "default":
            legacy = cache_dir() / "tla2tools.jar"
            if legacy.exists():
                targets.append(legacy)
            else:
                typer.echo("⚠ Warning: Default (legacy) tla2tools.jar not found.", err=True)
            continue

        matching = sorted([lv for lv in local_versions if lv.name == v], key=lambda x: x.path.name)
        if not matching:
            typer.echo(f"⚠ Warning: Version {v} not found locally.", err=True)
            continue

        if len(matching) > 1:
            typer.echo(f"Multiple versions match {v}:")
            for i, lv in enumerate(matching):
                typer.echo(f"[{i}] {lv.path.name}")
            choice = typer.prompt(f"Select build of {v} to uninstall (or 'all')", default="all")

            if str(choice).lower() == "all":
                targets.extend(lv.path for lv in matching)
            else:
                try:
                    idx = int(choice)
                    targets.append(matching[idx].path)
                except (ValueError, IndexError):
                    typer.echo("Invalid choice, skipping.", err=True)
        else:
            targets.append(matching[0].path)
    return targets


def _remove_path(path: Path, pinned_dir: Path | None) -> bool:
    """Remove a path (file or dir), returns True if it was the pinned version."""
    pinned_removed = False
    if pinned_dir and path.is_dir() and path.resolve() == pinned_dir.resolve():
        pinned_removed = True
        typer.echo(f"Note: {path.name} is currently pinned.")

    typer.echo(f"Removing {path.name} ...")
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    except OSError as e:
        typer.echo(f"Error: Failed to remove {path.name}: {e}", err=True)
    return pinned_removed


@app.command()
def uninstall(
    versions: list[str] = typer.Argument(None, help="One or more version tags to uninstall."),  # noqa: B008
    all_versions: bool = typer.Option(False, "--all", help="Uninstall ALL local versions (danger!)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """Remove one or more installed TLC versions from the local cache."""
    if all_versions:
        if not yes and not typer.confirm("This will delete ALL installed TLC versions. Are you sure?"):
            raise typer.Abort()
        targets = [lv.path for lv in list_local_versions()]
    else:
        if not versions:
            typer.echo("Error: Missing argument 'VERSIONS...'.", err=True)
            raise typer.Exit(1)
        targets = _resolve_uninstall_targets(versions)

    if not targets:
        typer.echo("No versions to uninstall.")
        return

    pinned_dir = get_pinned_version_dir()
    any_pinned_removed = any(_remove_path(p, pinned_dir) for p in targets)

    if any_pinned_removed:
        clear_pin()
        latest = resolve_latest_version(list_local_versions())
        if latest:
            set_pin(latest.path)
            typer.echo(f"Pin fell back to {latest.path.name}")
        else:
            typer.echo("No versions remaining, pin removed.")
