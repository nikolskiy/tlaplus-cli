import typer

from tlaplus_cli.cmd.tools import app
from tlaplus_cli.versioning import get_tools_dir


@app.command(name="dir")
def show_dir() -> None:
    """Show the absolute path to the local TLC tools cache directory."""
    tools_dir = get_tools_dir()
    typer.echo(str(tools_dir))

    if tools_dir.is_dir():
        versions = sorted([d.name for d in tools_dir.iterdir() if d.is_dir()])
        for v in versions:
            typer.echo(f"  {v}")
