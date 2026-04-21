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
