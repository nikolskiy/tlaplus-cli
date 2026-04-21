import typer

from tlaplus_cli.cmd.tools import app
from tlaplus_cli.versioning import get_tools_dir


@app.command(name="dir")
def show_dir() -> None:
    """Show the tools versions directory and its contents."""
    tools_dir = get_tools_dir()
    typer.echo(str(tools_dir))
    if tools_dir.exists():
        entries = sorted(d.name for d in tools_dir.iterdir() if d.is_dir() and not d.is_symlink())
        for entry in entries:
            typer.echo(f"  {entry}")
