import typer

from tlaplus_cli.cmd.tools.meta import app
from tlaplus_cli.config.loader import load_config
from tlaplus_cli.versioning import (
    fetch_remote_versions,
    list_local_versions,
    write_version_metadata,
)


@app.command(name="sync")
def meta_sync() -> None:
    """Synchronize local metadata with remote GitHub information."""
    config = load_config()
    versions, status = fetch_remote_versions(
        config.tla.urls.tags, config.tla.urls.releases, config.tla.urls.per_page
    )

    if not versions:
        typer.echo(f"Error: Could not fetch remote versions (status: {status.value})", err=True)
        raise typer.Exit(1)

    local_versions = list_local_versions()
    remote_map = {v.name: v for v in versions}

    for lv in local_versions:
        if lv.name in remote_map:
            target = remote_map[lv.name]
            write_version_metadata(lv.path, target)
            typer.echo(f"Synced metadata for {lv.path.name}")
        else:
            typer.echo(f"⚠ Warning: Could not find remote data for {lv.name}", err=True)

    typer.echo("Metadata sync complete.")
