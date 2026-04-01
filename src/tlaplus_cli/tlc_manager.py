import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tlaplus_cli.config import cache_dir, load_config
from tlaplus_cli.version_manager import (
    FetchStatus,
    LocalVersion,
    clear_cache,
    clear_pin,
    download_version,
    fetch_remote_versions,
    get_pinned_version_dir,
    get_tlc_dir,
    list_local_versions,
    read_version_metadata,
    resolve_latest_version,
    set_pin,
    write_version_metadata,
)

tlc_app = typer.Typer(help="Manage TLC versions")
meta_app = typer.Typer(help="Manage TLC metadata")
tlc_app.add_typer(meta_app, name="meta")
fetch_cache_app = typer.Typer(help="Manage GitHub API cache")


@tlc_app.command(name="list")
def list_versions() -> None:
    config = load_config()
    versions, status = fetch_remote_versions(config.tla.urls.tags, config.tla.urls.releases, config.tla.urls.per_page)

    local_versions = list_local_versions()
    pinned_dir = get_pinned_version_dir()
    pinned_dir_name = pinned_dir.name if pinned_dir else None

    # Track what we've displayed to handle local-only and duplicates
    # key: (name, short_sha)
    displayed: set[tuple[str, str]] = set()

    title = "TLC Versions"
    if status == FetchStatus.STALE:
        title += " (cached)"
    elif status == FetchStatus.UNAVAILABLE:
        typer.echo("⚠ remote data unavailable")

    table = Table(title=title)
    table.add_column("Version", style="cyan")
    table.add_column("Tag/SHA", style="magenta")
    table.add_column("Published", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Pinned", style="yellow", justify="center")

    def format_date(date_str: str) -> str:
        if not date_str:
            return ""
        return date_str.split("T", maxsplit=1)[0]

    if status == FetchStatus.UNAVAILABLE:
        for lv in local_versions:
            dir_name = f"{lv.name}-{lv.short_sha}"
            is_pinned = "[green]✓[/green]" if pinned_dir_name == dir_name else ""
            meta = read_version_metadata(lv.path)
            published = format_date(meta.get("published_at", "")) if meta else ""
            table.add_row(lv.name, lv.short_sha, published, "installed", is_pinned)
    else:
        remote_names = {v.name for v in versions}
        # First, remote versions
        for v in versions:
            dir_name = f"{v.name}-{v.short_sha}"
            is_pinned = "[green]✓[/green]" if pinned_dir_name == dir_name else ""

            # Check if this exact version (name+sha) is installed
            installed = any(lv.name == v.name and lv.short_sha == v.short_sha for lv in local_versions)
            row_status = "installed" if installed else "available"

            table.add_row(v.name, v.short_sha, format_date(v.published_at), row_status, is_pinned)
            displayed.add((v.name, v.short_sha))

        # Then, local versions not in remote (or with different SHAs)
        for lv in local_versions:
            if (lv.name, lv.short_sha) not in displayed:
                dir_name = f"{lv.name}-{lv.short_sha}"
                is_pinned = "[green]✓[/green]" if pinned_dir_name == dir_name else ""
                meta = read_version_metadata(lv.path)
                published = format_date(meta.get("published_at", "")) if meta else ""

                row_status = "installed" if lv.name in remote_names else "local only"
                table.add_row(lv.name, lv.short_sha, published, row_status, is_pinned)

    console = Console()
    console.print(table)


@tlc_app.command()
def install(
    version: str = typer.Argument(None),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download even if already installed."),
) -> None:
    config = load_config()
    versions, _ = fetch_remote_versions(config.tla.urls.tags, config.tla.urls.releases, config.tla.urls.per_page)
    if not versions:
        typer.echo("Error: Unable to fetch remote versions.", err=True)
        raise typer.Exit(1)

    if version:
        target = next((v for v in versions if v.name == version), None)
        if not target:
            typer.echo(f"Error: Version {version} not found in remote repository.", err=True)
            raise typer.Exit(1)
    else:
        target = versions[0]
        typer.echo(f"No version specified, selecting latest: {target.name}")

    version_dir = get_tlc_dir() / f"{target.name}-{target.short_sha}"
    jar_path = version_dir / "tla2tools.jar"

    if jar_path.exists() and not force:
        typer.echo(f"Version {target.name} ({target.short_sha}) is already installed.")
    else:
        try:
            version_dir = download_version(target, force=force)
            typer.echo("Download complete.")
        except Exception as e:
            typer.echo(f"Error: Failed to download: {e}", err=True)
            raise typer.Exit(1) from e

    pinned_dir = get_pinned_version_dir()
    if pinned_dir is None:
        typer.echo(f"Auto-pinning newly installed version {target.name}")
        set_pin(version_dir)


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


@tlc_app.command()
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


@tlc_app.command()
def path(version: str = typer.Argument(None)) -> None:
    """Show the path to tla2tools.jar for the pinned or specified version."""
    if not version:
        pinned_dir = get_pinned_version_dir()
        if pinned_dir:
            jar = pinned_dir / "tla2tools.jar"
            if jar.exists():
                _print_version_path(pinned_dir, jar)
                return
        typer.echo("Error: No pinned version found.", err=True)
        raise typer.Exit(1)

    for lv in list_local_versions():
        if lv.name == version:
            jar = lv.path / "tla2tools.jar"
            _print_version_path(lv.path, jar)
            return
    typer.echo(f"Error: Version {version} not found locally.", err=True)
    raise typer.Exit(1)


def _print_version_path(version_dir: Path, jar_path: Path) -> None:
    """Print the TLC2 version string (if available) and jar path."""
    meta = read_version_metadata(version_dir)
    if meta and meta.get("tlc2_version_string"):
        typer.echo(meta["tlc2_version_string"])
    typer.echo(str(jar_path))


@tlc_app.command()
def pin(version: str = typer.Argument(None)) -> None:
    local_versions = list_local_versions()
    if not local_versions:
        typer.echo("Error: No versions installed.", err=True)
        raise typer.Exit(1)

    if not version:
        typer.echo("Error: Please provide a version to pin.", err=True)
        raise typer.Exit(1)

    matching = [lv for lv in local_versions if lv.name == version]
    if not matching:
        typer.echo(f"Error: Version {version} not found locally.", err=True)
        raise typer.Exit(1)

    matching.sort(key=lambda x: x.path.name)

    if len(matching) > 1:
        typer.echo("Multiple versions match:")
        for i, lv in enumerate(matching):
            typer.echo(f"[{i}] {lv.path.name}")
        choice = typer.prompt("Select version to pin", type=int)
        if 0 <= choice < len(matching):
            target = matching[choice]
        else:
            typer.echo("Invalid choice.", err=True)
            raise typer.Exit(1)
    else:
        target = matching[0]

    set_pin(target.path)
    typer.echo(f"Pinned version set to {target.path.name}")


@tlc_app.command(name="dir")
def show_dir() -> None:
    """Show the TLC versions directory and its contents."""
    tlc_dir = get_tlc_dir()
    typer.echo(str(tlc_dir))
    if tlc_dir.exists():
        entries = sorted(d.name for d in tlc_dir.iterdir() if d.is_dir() and not d.is_symlink())
        for entry in entries:
            typer.echo(f"  {entry}")


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


@tlc_app.command()
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
                f"Version {lv.path.name} is currently pinned. Uninstalling it will break `tla run`. Continue?"
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


@fetch_cache_app.command(name="clear")
def cmd_clear_cache() -> None:
    clear_cache()
    typer.echo("GitHub API cache cleared.")


@meta_app.command(name="sync")
def meta_sync() -> None:
    config = load_config()
    versions, _ = fetch_remote_versions(config.tla.urls.tags, config.tla.urls.releases, config.tla.urls.per_page)
    local_versions = list_local_versions()

    for lv in local_versions:
        target = next((v for v in versions if v.name == lv.name), None)
        if target:
            write_version_metadata(lv.path, target)
            typer.echo(f"Synced metadata for {lv.path.name}")
        else:
            typer.echo(f"⚠ Warning: Could not find remote data for {lv.name}", err=True)
    typer.echo("Metadata sync complete.")
