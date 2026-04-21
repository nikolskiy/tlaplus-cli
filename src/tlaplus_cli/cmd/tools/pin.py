import typer

from tlaplus_cli.cmd.tools import app
from tlaplus_cli.versioning import list_local_versions, set_pin


@app.command()
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
