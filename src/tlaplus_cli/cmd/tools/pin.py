import typer

from tlaplus_cli.cmd.tools import app
from tlaplus_cli.versioning import list_local_versions, set_pin


@app.command()
def pin(version: str = typer.Argument(..., help="The version to pin (e.g. 'v1.8.0').")) -> None:
    """Pin a specific installed version to be used by 'tla tlc'."""
    local_versions = list_local_versions()

    matching = [lv for lv in local_versions if lv.name == version]

    if not matching:
        typer.echo(f"Error: Version {version} not found locally. Install it first.", err=True)
        raise typer.Exit(1)

    if len(matching) == 1:
        target = matching[0]
    else:
        typer.echo("Multiple versions match:")
        for i, lv in enumerate(matching):
            typer.echo(f"[{i}] {lv.path.name}")
        choice = typer.prompt("Select version to pin", type=int)
        if not (0 <= choice < len(matching)):
            typer.echo("Invalid choice.", err=True)
            raise typer.Exit(1)
        target = matching[choice]

    set_pin(target.path)
    typer.echo(f"Pinned version: {target.path.name}")
