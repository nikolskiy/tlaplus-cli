import typer

from tlaplus_cli.cmd.tools import app
from tlaplus_cli.config.loader import load_config
from tlaplus_cli.versioning import (
    download_version,
    download_version_from_url,
    fetch_remote_versions,
    get_pinned_version_dir,
    get_tools_dir,
    is_url,
    set_pin,
)


@app.command()
def install(
    version: str = typer.Argument(None),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download even if already installed."),
) -> None:
    # --- URL install branch ---
    if version and is_url(version):
        try:
            version_dir = download_version_from_url(version)
            typer.echo("Download complete.")
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from e
        except Exception as e:
            typer.echo(f"Error: Failed to download: {e}", err=True)
            raise typer.Exit(1) from e

        pinned_dir = get_pinned_version_dir()
        if pinned_dir is None:
            typer.echo(f"Auto-pinning newly installed version {version_dir.name}")
            set_pin(version_dir)
        return
    # --- end URL branch ---

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

    version_dir = get_tools_dir() / f"{target.name}-{target.short_sha}"
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
