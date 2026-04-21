from pathlib import Path

import typer

from tlaplus_cli.cmd.tools import app
from tlaplus_cli.versioning import get_pinned_version_dir, list_local_versions


@app.command()
def path(version: str = typer.Argument(None)) -> None:
    """Show the path to tla2tools.jar for the pinned or specified version."""
    if not version:
        pinned_dir = get_pinned_version_dir()
        if pinned_dir:
            jar = pinned_dir / "tla2tools.jar"
            if jar.exists():
                _print_version_path(jar)
                return
        typer.echo("Error: No pinned version found.", err=True)
        raise typer.Exit(1)

    for lv in list_local_versions():
        if lv.name == version:
            jar = lv.path / "tla2tools.jar"
            _print_version_path(jar)
            return
    typer.echo(f"Error: Version {version} not found locally.", err=True)
    raise typer.Exit(1)


def _print_version_path(jar_path: Path) -> None:
    """Print the absolute path to tla2tools.jar."""
    typer.echo(str(jar_path.absolute()))
